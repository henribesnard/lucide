"""
Circuit Breaker pattern pour protéger contre les cascades d'échecs API.

États:
- CLOSED : Fonctionnement normal
- OPEN : Trop d'échecs, appels bloqués
- HALF_OPEN : Test de récupération
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """États du circuit breaker"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenError(Exception):
    """Exception levée quand le circuit est ouvert"""
    pass


class CircuitBreaker:
    """
    Circuit Breaker pour protéger contre les cascades d'échecs.

    Paramètres:
        name: Nom du circuit (pour logging)
        failure_threshold: Nombre d'échecs avant ouverture (défaut: 5)
        timeout: Durée en secondes avant tentative de réinitialisation (défaut: 60)
        success_threshold: Nombre de succès en HALF_OPEN pour fermer (défaut: 2)

    Exemple:
        circuit = CircuitBreaker('api_football', failure_threshold=5, timeout=60)
        result = await circuit.call(api_function, arg1, arg2)
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout: int = 60,
        success_threshold: int = 2
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.last_failure_time: Optional[datetime] = None

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Exécuter un appel avec protection circuit breaker.

        Args:
            func: Fonction async à exécuter
            *args, **kwargs: Arguments à passer à la fonction

        Returns:
            Résultat de la fonction

        Raises:
            CircuitBreakerOpenError: Si le circuit est ouvert
            Exception: Toute exception levée par la fonction
        """

        # Vérifier l'état du circuit
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"Circuit {self.name}: Tentative de réinitialisation (HALF_OPEN)")
                self.state = CircuitState.HALF_OPEN
                self.successes = 0
            else:
                time_until_reset = self._time_until_reset()
                logger.warning(
                    f"Circuit {self.name}: OPEN, appel bloqué "
                    f"(réessayer dans {time_until_reset:.0f}s)"
                )
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Retry after {time_until_reset:.0f} seconds."
                )

        try:
            # Exécuter l'appel
            result = await func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            logger.error(
                f"Circuit {self.name}: Échec d'appel - {type(e).__name__}: {str(e)}"
            )
            raise

    def _on_success(self):
        """Gérer un appel réussi"""
        self.failures = 0

        if self.state == CircuitState.HALF_OPEN:
            self.successes += 1
            logger.info(
                f"Circuit {self.name}: Succès en HALF_OPEN "
                f"({self.successes}/{self.success_threshold})"
            )

            if self.successes >= self.success_threshold:
                logger.info(f"Circuit {self.name}: Réinitialisation complète (CLOSED)")
                self.state = CircuitState.CLOSED
                self.successes = 0
        elif self.state == CircuitState.CLOSED:
            logger.debug(f"Circuit {self.name}: Appel réussi (CLOSED)")

    def _on_failure(self):
        """Gérer un échec d'appel"""
        self.failures += 1
        self.last_failure_time = datetime.utcnow()

        if self.state == CircuitState.HALF_OPEN:
            logger.warning(
                f"Circuit {self.name}: Échec en HALF_OPEN, retour à OPEN"
            )
            self.state = CircuitState.OPEN
            self.successes = 0
        elif self.state == CircuitState.CLOSED:
            logger.warning(
                f"Circuit {self.name}: Échec {self.failures}/{self.failure_threshold}"
            )

            if self.failures >= self.failure_threshold:
                logger.error(
                    f"Circuit {self.name}: Seuil atteint, passage à OPEN "
                    f"(timeout: {self.timeout}s)"
                )
                self.state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Vérifier si on peut tenter de réinitialiser"""
        if not self.last_failure_time:
            return False

        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout

    def _time_until_reset(self) -> float:
        """Calculer le temps restant avant possibilité de reset"""
        if not self.last_failure_time:
            return 0.0

        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return max(0, self.timeout - elapsed)

    def get_state(self) -> dict:
        """
        Obtenir l'état actuel du circuit.

        Returns:
            Dict contenant l'état complet du circuit
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failures": self.failures,
            "successes": self.successes,
            "failure_threshold": self.failure_threshold,
            "success_threshold": self.success_threshold,
            "timeout": self.timeout,
            "last_failure": self.last_failure_time.isoformat()
                if self.last_failure_time else None,
            "time_until_reset": self._time_until_reset() if self.state == CircuitState.OPEN else None
        }

    def reset(self):
        """Réinitialiser manuellement le circuit (pour tests ou admin)"""
        logger.info(f"Circuit {self.name}: Réinitialisation manuelle")
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.last_failure_time = None


class CircuitBreakerManager:
    """
    Gestionnaire centralisé de circuit breakers.

    Permet de créer et gérer plusieurs circuit breakers par endpoint/service.
    """

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}

    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout: int = 60,
        success_threshold: int = 2
    ) -> CircuitBreaker:
        """
        Obtenir un circuit breaker existant ou en créer un nouveau.

        Args:
            name: Nom du circuit
            failure_threshold: Seuil d'échecs
            timeout: Timeout avant reset
            success_threshold: Succès requis en HALF_OPEN

        Returns:
            CircuitBreaker instance
        """
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                timeout=timeout,
                success_threshold=success_threshold
            )
            logger.info(f"Circuit Breaker créé: {name}")

        return self._breakers[name]

    def get_all_states(self) -> dict:
        """Obtenir l'état de tous les circuits"""
        return {
            name: breaker.get_state()
            for name, breaker in self._breakers.items()
        }

    def reset_all(self):
        """Réinitialiser tous les circuits (admin only)"""
        logger.warning("Réinitialisation de tous les circuit breakers")
        for breaker in self._breakers.values():
            breaker.reset()


# Instance globale pour l'application
circuit_breaker_manager = CircuitBreakerManager()
