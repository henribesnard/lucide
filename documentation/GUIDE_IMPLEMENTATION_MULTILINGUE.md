# Guide d'Implémentation du Système Multilingue (FR/EN)

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Implémentation Backend](#implémentation-backend)
4. [Implémentation Frontend](#implémentation-frontend)
5. [Tests](#tests)
6. [Migration](#migration)

---

## 🎯 Vue d'ensemble

Ce guide explique comment implémenter un système de sélection de langue (français/anglais) dans l'application Lucide, permettant aux utilisateurs de choisir leur langue préférée pour l'interface et les réponses du LLM.

### Objectifs

- ✅ Permettre la sélection de la langue dans le frontend (FR/EN)
- ✅ Transmettre la langue choisie au backend via les API calls
- ✅ Adapter les réponses du LLM selon la langue
- ✅ Traduire les messages système et erreurs
- ✅ Sauvegarder la préférence de langue par utilisateur

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      FRONTEND                            │
│  ┌─────────────────────────────────────────────────┐   │
│  │  1. Sélecteur de Langue (Dropdown/Toggle)       │   │
│  │     FR 🇫🇷  |  EN 🇬🇧                            │   │
│  └──────────────────┬──────────────────────────────┘   │
│                     │                                    │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │  2. Context State (language: 'fr' | 'en')       │   │
│  └──────────────────┬──────────────────────────────┘   │
│                     │                                    │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │  3. API Calls + language param                  │   │
│  │     POST /chat { message, context, language }   │   │
│  └──────────────────┬──────────────────────────────┘   │
└────────────────────┼────────────────────────────────────┘
                     │
                     │ HTTP Request
                     │ { language: 'fr' | 'en' }
                     │
┌────────────────────▼────────────────────────────────────┐
│                      BACKEND                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │  1. Endpoint /chat                              │   │
│  │     - Reçoit le paramètre language              │   │
│  │     - Valide: 'fr' | 'en' (default: 'fr')       │   │
│  └──────────────────┬──────────────────────────────┘   │
│                     │                                    │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │  2. Pipeline                                    │   │
│  │     - Passe language à tous les agents          │   │
│  └──────────────────┬──────────────────────────────┘   │
│                     │                                    │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │  3. LLM Prompts (prompts.py)                    │   │
│  │     - Adapte les prompts selon la langue        │   │
│  │     - Instructions en FR ou EN                  │   │
│  └──────────────────┬──────────────────────────────┘   │
│                     │                                    │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │  4. Response Agent                              │   │
│  │     - Génère réponse dans la langue demandée    │   │
│  └──────────────────┬──────────────────────────────┘   │
│                     │                                    │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │  5. User Preferences (DB)                       │   │
│  │     - Sauvegarde langue préférée                │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Implémentation Backend

### 1. Schéma de Données

#### `backend/store/schemas.py`

Ajouter le champ `preferred_language` au modèle User :

```python
from sqlalchemy import Column, String

class User(Base):
    __tablename__ = "users"

    # ... autres champs existants

    preferred_language = Column(String, nullable=False, default="fr")
    # Valeurs possibles: 'fr', 'en'
```

#### Migration Base de Données

```bash
# Créer une migration Alembic
alembic revision -m "add preferred_language to users"
```

Fichier de migration généré :

```python
def upgrade():
    op.add_column('users', sa.Column('preferred_language', sa.String(), nullable=False, server_default='fr'))

def downgrade():
    op.drop_column('users', 'preferred_language')
```

---

### 2. API Endpoints

#### `backend/routes/chat.py`

Modifier l'endpoint `/chat` pour accepter le paramètre `language` :

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional

class ChatRequest(BaseModel):
    message: str
    context: Optional[dict] = None
    language: Literal["fr", "en"] = Field(default="fr", description="Language for response")
    model_preference: Optional[str] = None

@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Chat endpoint with language support.
    """
    language = request.language or current_user.preferred_language or "fr"

    # Passer language au pipeline
    result = await pipeline.run(
        question=request.message,
        context=request.context,
        language=language,
        user_id=current_user.user_id,
        model_preference=request.model_preference,
    )

    return {
        "response": result.response,
        "language": language,
        "session_id": result.session_id,
        "intent": result.intent,
        "entities": result.entities,
        "tools": result.tools_used,
    }
```

#### `backend/routes/auth.py`

Ajouter endpoint pour mettre à jour la langue préférée :

```python
from pydantic import BaseModel

class UpdateLanguageRequest(BaseModel):
    language: Literal["fr", "en"]

@router.patch("/me/language")
async def update_language(
    request: UpdateLanguageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update user's preferred language.
    """
    current_user.preferred_language = request.language
    db.commit()

    return {
        "message": "Language updated successfully",
        "preferred_language": request.language
    }

@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get current user information including preferred language.
    """
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "preferred_language": current_user.preferred_language,
        "subscription_tier": current_user.subscription_tier,
    }
```

---

### 3. Pipeline et Agents

#### `backend/agents/pipeline.py`

Modifier le pipeline pour passer le paramètre `language` :

```python
from typing import Literal

async def run(
    self,
    question: str,
    context: Optional[Dict] = None,
    language: Literal["fr", "en"] = "fr",
    user_id: Optional[str] = None,
    model_preference: Optional[str] = None,
) -> PipelineResult:
    """
    Execute the full pipeline with language support.
    """
    # ... code existant

    # Passer language aux agents
    intent_result = await self.analysis_agent.analyze_intent(
        question=question,
        context=context,
        language=language,
    )

    # ... autres agents

    response = await self.response_agent.generate_response(
        question=question,
        intent=intent_result,
        tool_results=tool_results,
        context=enhanced_context,
        language=language,  # Passer language
        causal_result=causal_result,
    )
```

---

### 4. Prompts Multilingues

#### `backend/prompts.py`

Créer des prompts adaptés selon la langue :

```python
from typing import Literal

# Dictionnaire de traductions pour les prompts système
SYSTEM_PROMPTS = {
    "fr": {
        "intent_classification": """Tu es un assistant spécialisé dans l'analyse du football.
Ta tâche est de classifier l'intention de la question de l'utilisateur parmi les catégories suivantes:
- analyse_rencontre: analyse d'un match spécifique
- pronostic: prédiction du résultat d'un match
- stats_equipe: statistiques d'une équipe
- stats_joueur: statistiques d'un joueur
- classement: classement d'une ligue
...""",

        "response_generation": """Tu es Lucide, un assistant expert en football.
Réponds à la question de l'utilisateur de manière précise et détaillée en français.
Utilise les données fournies pour construire une réponse complète et structurée.""",

        "causal_analysis": """Tu es un analyste football expert en analyse causale.
Explique les causes et mécanismes derrière les résultats observés.""",
    },

    "en": {
        "intent_classification": """You are an assistant specialized in football analysis.
Your task is to classify the user's question intent among the following categories:
- analyse_rencontre: specific match analysis
- pronostic: match result prediction
- stats_equipe: team statistics
- stats_joueur: player statistics
- classement: league standings
...""",

        "response_generation": """You are Lucide, an expert football assistant.
Answer the user's question accurately and in detail in English.
Use the provided data to build a complete and structured response.""",

        "causal_analysis": """You are an expert football analyst specialized in causal analysis.
Explain the causes and mechanisms behind the observed results.""",
    }
}

def get_system_prompt(prompt_type: str, language: Literal["fr", "en"] = "fr") -> str:
    """
    Get system prompt in the specified language.
    """
    return SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["fr"]).get(prompt_type, "")

def get_intent_classification_prompt(question: str, language: Literal["fr", "en"] = "fr") -> str:
    """
    Build intent classification prompt in the specified language.
    """
    system_prompt = get_system_prompt("intent_classification", language)

    if language == "en":
        user_prompt = f"Classify the following question:\n\n{question}"
    else:
        user_prompt = f"Classifie la question suivante :\n\n{question}"

    return system_prompt + "\n\n" + user_prompt

def get_response_prompt(
    question: str,
    context: str,
    language: Literal["fr", "en"] = "fr"
) -> str:
    """
    Build response generation prompt in the specified language.
    """
    system_prompt = get_system_prompt("response_generation", language)

    if language == "en":
        return f"""{system_prompt}

## Context
{context}

## User Question
{question}

## Instructions
Provide a detailed, accurate, and well-structured answer in English.
"""
    else:
        return f"""{system_prompt}

## Contexte
{context}

## Question de l'utilisateur
{question}

## Instructions
Fournis une réponse détaillée, précise et bien structurée en français.
"""
```

---

### 5. Agents Modifiés

#### `backend/agents/analysis_agent.py`

```python
async def analyze_intent(
    self,
    question: str,
    context: Optional[Dict] = None,
    language: Literal["fr", "en"] = "fr",
) -> IntentResult:
    """
    Analyze user intent with language support.
    """
    prompt = get_intent_classification_prompt(question, language=language)

    # ... reste du code
```

#### `backend/agents/response_agent.py`

```python
async def generate_response(
    self,
    question: str,
    intent: IntentResult,
    tool_results: List[ToolCallResult],
    context: Optional[Dict] = None,
    language: Literal["fr", "en"] = "fr",
    causal_result: Optional[CausalAnalysisResult] = None,
) -> str:
    """
    Generate response in the specified language.
    """
    prompt = get_response_prompt(
        question=question,
        context=self._format_context(tool_results, context, causal_result),
        language=language,
    )

    messages = [
        {"role": "system", "content": get_system_prompt("response_generation", language)},
        {"role": "user", "content": prompt},
    ]

    response = await self.llm.chat_completion(
        messages=messages,
        temperature=0.7,
        max_tokens=2000,
    )

    return response.choices[0].message.content.strip()
```

---

### 6. Messages d'Erreur Multilingues

#### `backend/utils/i18n.py` (nouveau fichier)

```python
from typing import Literal

ERROR_MESSAGES = {
    "fr": {
        "not_authenticated": "Non authentifié",
        "invalid_credentials": "Identifiants invalides",
        "match_not_found": "Match non trouvé",
        "team_not_found": "Équipe non trouvée",
        "player_not_found": "Joueur non trouvé",
        "invalid_language": "Langue invalide. Utilisez 'fr' ou 'en'",
        "server_error": "Erreur serveur interne",
    },
    "en": {
        "not_authenticated": "Not authenticated",
        "invalid_credentials": "Invalid credentials",
        "match_not_found": "Match not found",
        "team_not_found": "Team not found",
        "player_not_found": "Player not found",
        "invalid_language": "Invalid language. Use 'fr' or 'en'",
        "server_error": "Internal server error",
    }
}

def get_error_message(error_key: str, language: Literal["fr", "en"] = "fr") -> str:
    """
    Get error message in the specified language.
    """
    return ERROR_MESSAGES.get(language, ERROR_MESSAGES["fr"]).get(
        error_key,
        ERROR_MESSAGES[language]["server_error"]
    )
```

Utilisation dans les routes :

```python
from backend.utils.i18n import get_error_message

@router.post("/chat")
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    try:
        # ... code
        pass
    except Exception as e:
        language = request.language or "fr"
        raise HTTPException(
            status_code=500,
            detail=get_error_message("server_error", language)
        )
```

---

## 💻 Implémentation Frontend

### 1. Types TypeScript

#### `frontend/src/types/language.ts`

```typescript
export type Language = 'fr' | 'en';

export interface LanguageConfig {
  code: Language;
  name: string;
  flag: string;
}

export const AVAILABLE_LANGUAGES: LanguageConfig[] = [
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'en', name: 'English', flag: '🇬🇧' },
];
```

---

### 2. Context de Langue

#### `frontend/src/contexts/LanguageContext.tsx`

```typescript
import React, { createContext, useContext, useState, useEffect } from 'react';
import { Language } from '../types/language';
import { useAuth } from './AuthContext';
import { apiClient } from '../api/client';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => Promise<void>;
  isLoading: boolean;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [language, setLanguageState] = useState<Language>('fr');
  const [isLoading, setIsLoading] = useState(false);

  // Charger la langue préférée de l'utilisateur au montage
  useEffect(() => {
    if (user?.preferred_language) {
      setLanguageState(user.preferred_language as Language);
    } else {
      // Fallback: langue du navigateur
      const browserLang = navigator.language.split('-')[0];
      setLanguageState(browserLang === 'en' ? 'en' : 'fr');
    }
  }, [user]);

  const setLanguage = async (lang: Language) => {
    setIsLoading(true);
    try {
      setLanguageState(lang);
      localStorage.setItem('preferred_language', lang);

      // Mettre à jour la préférence côté serveur si connecté
      if (user) {
        await apiClient.patch('/auth/me/language', { language: lang });
      }
    } catch (error) {
      console.error('Failed to update language:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, isLoading }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider');
  }
  return context;
};
```

---

### 3. Composant Sélecteur de Langue

#### `frontend/src/components/LanguageSelector.tsx`

```typescript
import React from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { AVAILABLE_LANGUAGES } from '../types/language';

export const LanguageSelector: React.FC = () => {
  const { language, setLanguage, isLoading } = useLanguage();

  return (
    <div className="language-selector">
      <select
        value={language}
        onChange={(e) => setLanguage(e.target.value as Language)}
        disabled={isLoading}
        className="language-dropdown"
      >
        {AVAILABLE_LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.flag} {lang.name}
          </option>
        ))}
      </select>
    </div>
  );
};
```

Style CSS :

```css
.language-selector {
  position: relative;
}

.language-dropdown {
  padding: 8px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.language-dropdown:hover {
  border-color: #3b82f6;
}

.language-dropdown:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

---

### 4. Intégration dans les API Calls

#### `frontend/src/api/client.ts`

Modifier le client API pour inclure automatiquement la langue :

```typescript
import axios from 'axios';
import { Language } from '../types/language';

class APIClient {
  private baseURL: string;
  private currentLanguage: Language = 'fr';

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  setLanguage(language: Language) {
    this.currentLanguage = language;
  }

  async post(endpoint: string, data: any) {
    return axios.post(`${this.baseURL}${endpoint}`, {
      ...data,
      language: this.currentLanguage,
    }, {
      headers: {
        'Authorization': `Bearer ${this.getToken()}`,
        'Content-Type': 'application/json',
      }
    });
  }

  // ... autres méthodes
}

export const apiClient = new APIClient(process.env.REACT_APP_API_URL || 'http://localhost:8001');
```

#### `frontend/src/hooks/useChat.ts`

```typescript
import { useLanguage } from '../contexts/LanguageContext';
import { apiClient } from '../api/client';

export const useChat = () => {
  const { language } = useLanguage();

  const sendMessage = async (message: string, context?: any) => {
    // La langue est automatiquement ajoutée par apiClient
    apiClient.setLanguage(language);

    const response = await apiClient.post('/chat', {
      message,
      context,
      // language sera ajouté automatiquement
    });

    return response.data;
  };

  return { sendMessage };
};
```

---

### 5. Traductions UI

#### `frontend/src/i18n/translations.ts`

```typescript
import { Language } from '../types/language';

export const translations = {
  fr: {
    common: {
      search: 'Rechercher',
      loading: 'Chargement...',
      error: 'Erreur',
      cancel: 'Annuler',
      save: 'Enregistrer',
    },
    chat: {
      placeholder: 'Posez votre question sur le football...',
      send: 'Envoyer',
      clearHistory: 'Effacer l\'historique',
    },
    context: {
      league: 'Ligue',
      team: 'Équipe',
      match: 'Match',
      player: 'Joueur',
    },
    settings: {
      language: 'Langue',
      theme: 'Thème',
      notifications: 'Notifications',
    },
  },
  en: {
    common: {
      search: 'Search',
      loading: 'Loading...',
      error: 'Error',
      cancel: 'Cancel',
      save: 'Save',
    },
    chat: {
      placeholder: 'Ask your football question...',
      send: 'Send',
      clearHistory: 'Clear history',
    },
    context: {
      league: 'League',
      team: 'Team',
      match: 'Match',
      player: 'Player',
    },
    settings: {
      language: 'Language',
      theme: 'Theme',
      notifications: 'Notifications',
    },
  },
};

export const useTranslation = (language: Language) => {
  return {
    t: (key: string) => {
      const keys = key.split('.');
      let value: any = translations[language];

      for (const k of keys) {
        value = value?.[k];
      }

      return value || key;
    }
  };
};
```

Utilisation :

```typescript
import { useLanguage } from '../contexts/LanguageContext';
import { useTranslation } from '../i18n/translations';

const MyComponent = () => {
  const { language } = useLanguage();
  const { t } = useTranslation(language);

  return (
    <div>
      <h1>{t('chat.placeholder')}</h1>
      <button>{t('chat.send')}</button>
    </div>
  );
};
```

---

### 6. Intégration dans App.tsx

```typescript
import React from 'react';
import { LanguageProvider } from './contexts/LanguageContext';
import { AuthProvider } from './contexts/AuthProvider';
import { LanguageSelector } from './components/LanguageSelector';

function App() {
  return (
    <AuthProvider>
      <LanguageProvider>
        <div className="app">
          <header>
            <LanguageSelector />
          </header>
          {/* Reste de l'application */}
        </div>
      </LanguageProvider>
    </AuthProvider>
  );
}

export default App;
```

---

## 🧪 Tests

### 1. Tests Backend

#### `backend/tests/test_language.py`

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_chat_with_language_fr(client: AsyncClient, auth_token: str):
    response = await client.post(
        "/chat",
        json={
            "message": "Quel est le classement de la Premier League?",
            "language": "fr"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "fr"
    # Vérifier que la réponse est en français
    assert "classement" in data["response"].lower() or "premier league" in data["response"].lower()

@pytest.mark.asyncio
async def test_chat_with_language_en(client: AsyncClient, auth_token: str):
    response = await client.post(
        "/chat",
        json={
            "message": "What is the Premier League standings?",
            "language": "en"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "en"
    # Vérifier que la réponse est en anglais
    assert "standings" in data["response"].lower() or "premier league" in data["response"].lower()

@pytest.mark.asyncio
async def test_update_preferred_language(client: AsyncClient, auth_token: str):
    response = await client.patch(
        "/auth/me/language",
        json={"language": "en"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    assert response.json()["preferred_language"] == "en"

    # Vérifier que la langue est sauvegardée
    user_info = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert user_info.json()["preferred_language"] == "en"
```

### 2. Tests Frontend

#### `frontend/src/components/__tests__/LanguageSelector.test.tsx`

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { LanguageSelector } from '../LanguageSelector';
import { LanguageProvider } from '../../contexts/LanguageContext';

describe('LanguageSelector', () => {
  it('renders language options', () => {
    render(
      <LanguageProvider>
        <LanguageSelector />
      </LanguageProvider>
    );

    expect(screen.getByText(/Français/)).toBeInTheDocument();
    expect(screen.getByText(/English/)).toBeInTheDocument();
  });

  it('changes language on selection', async () => {
    render(
      <LanguageProvider>
        <LanguageSelector />
      </LanguageProvider>
    );

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'en' } });

    expect(select).toHaveValue('en');
  });
});
```

---

## 📦 Migration

### Étapes de Migration

1. **Base de données**
   ```bash
   # Créer et appliquer la migration
   alembic revision -m "add preferred_language to users"
   alembic upgrade head
   ```

2. **Backend**
   - Ajouter le champ `language` aux endpoints existants
   - Créer `backend/utils/i18n.py`
   - Modifier `backend/prompts.py` pour les prompts multilingues
   - Mettre à jour tous les agents pour accepter le paramètre `language`

3. **Frontend**
   - Créer le `LanguageContext`
   - Ajouter le `LanguageSelector` dans le header
   - Créer les fichiers de traduction
   - Modifier les appels API pour inclure la langue

4. **Tests**
   - Tester les deux langues (FR/EN) sur tous les endpoints
   - Vérifier la sauvegarde de la préférence utilisateur
   - Valider les traductions UI

---

## 📝 Checklist d'Implémentation

### Backend
- [ ] Migration DB ajoutée (preferred_language)
- [ ] Schéma User mis à jour
- [ ] Endpoint /auth/me/language créé
- [ ] Endpoint /chat modifié (paramètre language)
- [ ] Pipeline modifié pour passer language
- [ ] Prompts multilingues créés
- [ ] Agents modifiés (language param)
- [ ] Messages d'erreur traduits
- [ ] Tests backend écrits

### Frontend
- [ ] Types Language créés
- [ ] LanguageContext implémenté
- [ ] LanguageSelector créé
- [ ] API client modifié (auto-include language)
- [ ] Fichiers de traduction créés
- [ ] Hook useTranslation implémenté
- [ ] Intégration dans App.tsx
- [ ] Tests frontend écrits

### Tests
- [ ] Tests API avec FR
- [ ] Tests API avec EN
- [ ] Tests mise à jour préférence
- [ ] Tests composants UI
- [ ] Tests bout-en-bout (E2E)

---

## 🚀 Déploiement

1. **Développement**
   ```bash
   # Backend
   cd backend
   alembic upgrade head
   uvicorn backend.main:app --reload

   # Frontend
   cd frontend
   npm install
   npm start
   ```

2. **Production**
   ```bash
   # Migration DB
   alembic upgrade head

   # Rebuild containers
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

3. **Vérification**
   - Tester la sélection de langue dans l'UI
   - Vérifier que les réponses sont dans la bonne langue
   - Confirmer la sauvegarde de la préférence

---

## 🎯 Résultat Attendu

### Frontend
- Sélecteur de langue visible dans le header (🇫🇷/🇬🇧)
- Interface traduite selon la langue choisie
- Préférence sauvegardée entre les sessions

### Backend
- Réponses LLM dans la langue demandée
- Messages d'erreur traduits
- Préférence stockée en base de données

### Expérience Utilisateur
1. Utilisateur sélectionne "English" 🇬🇧
2. L'interface se traduit immédiatement
3. Les questions sont envoyées avec `language: "en"`
4. Les réponses du LLM sont en anglais
5. La préférence est sauvegardée automatiquement

---

## 📚 Ressources

- [i18next](https://www.i18next.com/) - Alternative robuste pour la gestion des traductions
- [react-i18next](https://react.i18next.com/) - Intégration React pour i18next
- [FastAPI i18n](https://fastapi.tiangolo.com/advanced/custom-response/) - Internationalisation FastAPI

---

**Date**: 2025-12-25
**Version**: 1.0
**Auteur**: Claude Sonnet 4.5
