"""
Verrous distribués Redis pour prévenir les race conditions.

Utilise Redis pour garantir qu'un seul processus peut modifier un contexte à la fois.
"""

import asyncio
import logging
import uuid
from typing import Optional
from datetime import datetime, timedelta
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class DistributedLockError(Exception):
    """Exception levée quand un verrou ne peut pas être acquis"""
    pass


class DistributedLock:
    """
    Verrou distribué basé sur Redis.

    Utilise l'algorithme Redlock pour garantir l'exclusion mutuelle.

    Parameters:
        redis_client: Client Redis async
        resource: Nom de la ressource à verrouiller
        ttl: Durée de vie du verrou en secondes (défaut: 10s)
        retry_times: Nombre de tentatives (défaut: 3)
        retry_delay: Délai entre tentatives en secondes (défaut: 0.2s)

    Example:
        async with DistributedLock(redis_client, f"context:{context_id}"):
            # Code critique protégé
            await context_manager.enrich_context(...)
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        resource: str,
        ttl: int = 10,
        retry_times: int = 3,
        retry_delay: float = 0.2
    ):
        self.redis = redis_client
        self.resource = resource
        self.ttl = ttl
        self.retry_times = retry_times
        self.retry_delay = retry_delay

        # Identifiant unique pour ce verrou
        self.lock_id = str(uuid.uuid4())
        self.acquired = False

    async def __aenter__(self):
        """Acquérir le verrou (context manager)"""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Libérer le verrou (context manager)"""
        await self.release()
        return False

    async def acquire(self) -> bool:
        """
        Tenter d'acquérir le verrou avec retry.

        Returns:
            True si le verrou a été acquis

        Raises:
            DistributedLockError: Si le verrou n'a pas pu être acquis
        """
        for attempt in range(self.retry_times):
            try:
                # Tenter d'acquérir le verrou avec SET NX EX
                # NX = only set if not exists
                # EX = expiration en secondes
                acquired = await self.redis.set(
                    name=f"lock:{self.resource}",
                    value=self.lock_id,
                    ex=self.ttl,
                    nx=True
                )

                if acquired:
                    self.acquired = True
                    logger.debug(
                        f"Verrou acquis: {self.resource} "
                        f"(id={self.lock_id[:8]}, ttl={self.ttl}s)"
                    )
                    return True

                # Verrou déjà pris, attendre avant retry
                if attempt < self.retry_times - 1:
                    logger.debug(
                        f"Verrou occupé: {self.resource}, "
                        f"retry {attempt + 1}/{self.retry_times}"
                    )
                    await asyncio.sleep(self.retry_delay)

            except redis.RedisError as e:
                logger.error(f"Erreur Redis lors de l'acquisition: {e}")
                if attempt < self.retry_times - 1:
                    await asyncio.sleep(self.retry_delay)

        # Échec après tous les retries
        logger.warning(
            f"Impossible d'acquérir le verrou: {self.resource} "
            f"après {self.retry_times} tentatives"
        )
        raise DistributedLockError(
            f"Failed to acquire lock for '{self.resource}' "
            f"after {self.retry_times} attempts"
        )

    async def release(self):
        """
        Libérer le verrou.

        Utilise un script Lua pour garantir qu'on ne libère que
        notre propre verrou (vérification de l'ID).
        """
        if not self.acquired:
            return

        try:
            # Script Lua pour libération atomique
            # Ne libère que si la valeur correspond à notre lock_id
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """

            result = await self.redis.eval(
                lua_script,
                1,  # nombre de clés
                f"lock:{self.resource}",  # KEYS[1]
                self.lock_id  # ARGV[1]
            )

            if result == 1:
                logger.debug(
                    f"Verrou libéré: {self.resource} (id={self.lock_id[:8]})"
                )
            else:
                logger.warning(
                    f"Verrou déjà expiré ou pris par un autre processus: "
                    f"{self.resource}"
                )

            self.acquired = False

        except redis.RedisError as e:
            logger.error(f"Erreur Redis lors de la libération: {e}")

    async def extend(self, additional_ttl: int = 10) -> bool:
        """
        Étendre la durée de vie du verrou.

        Utile pour les opérations longues.

        Args:
            additional_ttl: Secondes à ajouter au TTL

        Returns:
            True si le verrou a été étendu
        """
        if not self.acquired:
            return False

        try:
            # Script Lua pour extension atomique
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("expire", KEYS[1], ARGV[2])
            else
                return 0
            end
            """

            result = await self.redis.eval(
                lua_script,
                1,
                f"lock:{self.resource}",
                self.lock_id,
                str(self.ttl + additional_ttl)
            )

            if result == 1:
                self.ttl += additional_ttl
                logger.debug(
                    f"Verrou étendu: {self.resource} "
                    f"(nouveau ttl={self.ttl}s)"
                )
                return True
            else:
                logger.warning(
                    f"Impossible d'étendre le verrou: {self.resource}"
                )
                return False

        except redis.RedisError as e:
            logger.error(f"Erreur Redis lors de l'extension: {e}")
            return False


class LockManager:
    """
    Gestionnaire de verrous distribués.

    Fournit une interface simple pour créer des verrous.
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def lock(
        self,
        resource: str,
        ttl: int = 10,
        retry_times: int = 3,
        retry_delay: float = 0.2
    ) -> DistributedLock:
        """
        Créer un verrou distribué.

        Args:
            resource: Nom de la ressource à verrouiller
            ttl: Durée de vie du verrou en secondes
            retry_times: Nombre de tentatives
            retry_delay: Délai entre tentatives

        Returns:
            DistributedLock instance

        Example:
            async with lock_manager.lock(f"context:{context_id}"):
                # Code critique
        """
        return DistributedLock(
            redis_client=self.redis,
            resource=resource,
            ttl=ttl,
            retry_times=retry_times,
            retry_delay=retry_delay
        )

    async def is_locked(self, resource: str) -> bool:
        """
        Vérifier si une ressource est verrouillée.

        Args:
            resource: Nom de la ressource

        Returns:
            True si la ressource est verrouillée
        """
        try:
            exists = await self.redis.exists(f"lock:{resource}")
            return exists == 1
        except redis.RedisError as e:
            logger.error(f"Erreur lors de la vérification du verrou: {e}")
            return False

    async def get_lock_info(self, resource: str) -> Optional[dict]:
        """
        Obtenir les informations sur un verrou.

        Args:
            resource: Nom de la ressource

        Returns:
            Dict avec les infos du verrou ou None
        """
        try:
            lock_key = f"lock:{resource}"
            lock_id = await self.redis.get(lock_key)

            if not lock_id:
                return None

            ttl = await self.redis.ttl(lock_key)

            return {
                "resource": resource,
                "lock_id": lock_id.decode() if isinstance(lock_id, bytes) else lock_id,
                "ttl_seconds": ttl,
                "locked": True
            }

        except redis.RedisError as e:
            logger.error(f"Erreur lors de la récupération des infos: {e}")
            return None

    async def force_release(self, resource: str) -> bool:
        """
        Forcer la libération d'un verrou (admin only).

        ATTENTION: À utiliser uniquement en cas de deadlock détecté.

        Args:
            resource: Nom de la ressource

        Returns:
            True si le verrou a été libéré
        """
        try:
            deleted = await self.redis.delete(f"lock:{resource}")
            if deleted:
                logger.warning(
                    f"Verrou forcé à être libéré (admin): {resource}"
                )
            return deleted == 1

        except redis.RedisError as e:
            logger.error(f"Erreur lors de la libération forcée: {e}")
            return False

    async def get_all_locks(self) -> list[dict]:
        """
        Obtenir la liste de tous les verrous actifs.

        Returns:
            Liste de dicts avec les infos de chaque verrou
        """
        try:
            # Scan tous les verrous
            locks = []
            cursor = 0

            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match="lock:*",
                    count=100
                )

                for key in keys:
                    key_str = key.decode() if isinstance(key, bytes) else key
                    resource = key_str.replace("lock:", "")
                    lock_info = await self.get_lock_info(resource)
                    if lock_info:
                        locks.append(lock_info)

                if cursor == 0:
                    break

            return locks

        except redis.RedisError as e:
            logger.error(f"Erreur lors de la récupération des verrous: {e}")
            return []
