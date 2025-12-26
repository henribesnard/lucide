import { Language } from '@/contexts/LanguageContext';

export interface Translations {
  // Navigation & Layout
  appTitle: string;
  home: string;
  chat: string;
  history: string;
  archives: string;
  settings: string;
  logout: string;
  profile: string;
  user: string;
  closeMenu: string;

  // Auth
  login: string;
  register: string;
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  confirmPassword: string;
  forgotPassword: string;
  alreadyHaveAccount: string;
  dontHaveAccount: string;
  loginButton: string;
  registerButton: string;
  loginTitle: string;
  loginSubtitle: string;
  loggingIn: string;
  createAccount: string;
  emailPlaceholder: string;
  registerTitle: string;
  registerSubtitle: string;
  registering: string;
  registerSuccess: string;
  fullName: string;
  fullNamePlaceholder: string;

  // Chat
  typeMessage: string;
  sendMessage: string;
  newChat: string;
  chatPlaceholder: string;
  selectModel: string;
  modelSlow: string;
  modelMedium: string;
  modelFast: string;
  assistantFootball: string;

  // Conversations
  conversations: string;
  archivedConversations: string;
  noConversations: string;
  noConversationsToday: string;
  noConversationsThisWeek: string;
  noArchivedConversations: string;
  deleteConversation: string;
  archiveConversation: string;
  restoreConversation: string;
  renameConversation: string;

  // Date labels
  today: string;
  yesterday: string;
  thisWeek: string;

  // Context selectors
  selectLeague: string;
  selectTeam: string;
  selectMatch: string;
  selectPlayer: string;
  searchLeague: string;
  searchTeam: string;
  searchPlayer: string;
  noLeaguesFound: string;
  noTeamsFound: string;
  noMatchesFound: string;
  noPlayersFound: string;

  // Settings
  languageSettings: string;
  selectLanguage: string;
  french: string;
  english: string;
  spanish: string;
  accountSettings: string;
  subscriptionSettings: string;
  theme: string;
  light: string;
  dark: string;
  auto: string;

  // Model types
  modelSlowDescription: string;
  modelMediumDescription: string;
  modelFastDescription: string;

  // Common
  loading: string;
  error: string;
  save: string;
  cancel: string;
  delete: string;
  edit: string;
  search: string;
  close: string;
  back: string;
  next: string;
  submit: string;
  confirm: string;
}

const translations: Record<Language, Translations> = {
  fr: {
    // Navigation & Layout
    appTitle: 'Lucide',
    home: 'Accueil',
    chat: 'Chat',
    history: 'Historique',
    archives: 'Archives',
    settings: 'Paramètres',
    logout: 'Déconnexion',
    profile: 'Profil',
    user: 'Utilisateur',
    closeMenu: 'Fermer le menu',

    // Auth
    login: 'Connexion',
    register: 'Inscription',
    email: 'Email',
    password: 'Mot de passe',
    firstName: 'Prénom',
    lastName: 'Nom',
    confirmPassword: 'Confirmer le mot de passe',
    forgotPassword: 'Mot de passe oublié ?',
    alreadyHaveAccount: 'Vous avez déjà un compte ?',
    dontHaveAccount: 'Vous n\'avez pas de compte ?',
    loginButton: 'Se connecter',
    registerButton: 'S\'inscrire',
    loginTitle: 'Connexion',
    loginSubtitle: 'Accédez à votre espace de travail.',
    loggingIn: 'Connexion...',
    createAccount: 'Créer un compte',
    emailPlaceholder: 'vous@email.com',
    registerTitle: 'Créer un compte',
    registerSubtitle: 'Démarrez avec STATOS pour vos analyses.',
    registering: 'Création...',
    registerSuccess: 'Compte créé. Vérifiez votre email.',
    fullName: 'Nom complet',
    fullNamePlaceholder: 'Prénom Nom',

    // Chat
    typeMessage: 'Tapez votre message...',
    sendMessage: 'Envoyer',
    newChat: 'Nouvelle conversation',
    chatPlaceholder: 'Posez une question sur le football...',
    selectModel: 'Sélectionner le modèle',
    modelSlow: 'Lent (DeepSeek)',
    modelMedium: 'Moyen (GPT-4o-mini)',
    modelFast: 'Rapide (GPT-4o)',
    assistantFootball: 'Assistant Football',

    // Conversations
    conversations: 'Conversations',
    archivedConversations: 'Conversations archivées',
    noConversations: 'Aucune conversation',
    noConversationsToday: 'Aucune conversation aujourd\'hui.',
    noConversationsThisWeek: 'Aucune conversation cette semaine.',
    noArchivedConversations: 'Aucune conversation archivée',
    deleteConversation: 'Supprimer la conversation',
    archiveConversation: 'Archiver la conversation',
    restoreConversation: 'Restaurer la conversation',
    renameConversation: 'Renommer la conversation',

    // Date labels
    today: 'Aujourd\'hui',
    yesterday: 'Hier',
    thisWeek: 'Cette semaine',

    // Context selectors
    selectLeague: 'Sélectionner une ligue',
    selectTeam: 'Sélectionner une équipe',
    selectMatch: 'Sélectionner un match',
    selectPlayer: 'Sélectionner un joueur',
    searchLeague: 'Rechercher une ligue...',
    searchTeam: 'Rechercher une équipe...',
    searchPlayer: 'Rechercher un joueur...',
    noLeaguesFound: 'Aucune ligue trouvée',
    noTeamsFound: 'Aucune équipe trouvée',
    noMatchesFound: 'Aucun match trouvé',
    noPlayersFound: 'Aucun joueur trouvé',

    // Settings
    languageSettings: 'Langue',
    selectLanguage: 'Sélectionner la langue',
    french: 'Français',
    english: 'Anglais',
    spanish: 'Espagnol',
    accountSettings: 'Compte',
    subscriptionSettings: 'Abonnement',
    theme: 'Thème',
    light: 'Clair',
    dark: 'Sombre',
    auto: 'Auto',

    // Model types
    modelSlowDescription: 'Économique, idéal pour les questions simples',
    modelMediumDescription: 'Équilibré entre rapidité et qualité',
    modelFastDescription: 'Premium, meilleure qualité et rapidité',

    // Common
    loading: 'Chargement...',
    error: 'Erreur',
    save: 'Enregistrer',
    cancel: 'Annuler',
    delete: 'Supprimer',
    edit: 'Modifier',
    search: 'Rechercher',
    close: 'Fermer',
    back: 'Retour',
    next: 'Suivant',
    submit: 'Soumettre',
    confirm: 'Confirmer',
  },
  en: {
    // Navigation & Layout
    appTitle: 'Lucide',
    home: 'Home',
    chat: 'Chat',
    history: 'History',
    archives: 'Archives',
    settings: 'Settings',
    logout: 'Logout',
    profile: 'Profile',
    user: 'User',
    closeMenu: 'Close menu',

    // Auth
    login: 'Login',
    register: 'Register',
    email: 'Email',
    password: 'Password',
    firstName: 'First Name',
    lastName: 'Last Name',
    confirmPassword: 'Confirm Password',
    forgotPassword: 'Forgot password?',
    alreadyHaveAccount: 'Already have an account?',
    dontHaveAccount: 'Don\'t have an account?',
    loginButton: 'Log in',
    registerButton: 'Sign up',
    loginTitle: 'Login',
    loginSubtitle: 'Access your workspace.',
    loggingIn: 'Logging in...',
    createAccount: 'Create account',
    emailPlaceholder: 'you@email.com',
    registerTitle: 'Create account',
    registerSubtitle: 'Get started with STATOS for your analysis.',
    registering: 'Creating...',
    registerSuccess: 'Account created. Check your email.',
    fullName: 'Full name',
    fullNamePlaceholder: 'First Last',

    // Chat
    typeMessage: 'Type your message...',
    sendMessage: 'Send',
    newChat: 'New conversation',
    chatPlaceholder: 'Ask a question about football...',
    selectModel: 'Select model',
    modelSlow: 'Slow (DeepSeek)',
    modelMedium: 'Medium (GPT-4o-mini)',
    modelFast: 'Fast (GPT-4o)',
    assistantFootball: 'Football Assistant',

    // Conversations
    conversations: 'Conversations',
    archivedConversations: 'Archived conversations',
    noConversations: 'No conversations',
    noConversationsToday: 'No conversations today.',
    noConversationsThisWeek: 'No conversations this week.',
    noArchivedConversations: 'No archived conversations',
    deleteConversation: 'Delete conversation',
    archiveConversation: 'Archive conversation',
    restoreConversation: 'Restore conversation',
    renameConversation: 'Rename conversation',

    // Date labels
    today: 'Today',
    yesterday: 'Yesterday',
    thisWeek: 'This week',

    // Context selectors
    selectLeague: 'Select a league',
    selectTeam: 'Select a team',
    selectMatch: 'Select a match',
    selectPlayer: 'Select a player',
    searchLeague: 'Search league...',
    searchTeam: 'Search team...',
    searchPlayer: 'Search player...',
    noLeaguesFound: 'No leagues found',
    noTeamsFound: 'No teams found',
    noMatchesFound: 'No matches found',
    noPlayersFound: 'No players found',

    // Settings
    languageSettings: 'Language',
    selectLanguage: 'Select language',
    french: 'French',
    english: 'English',
    spanish: 'Spanish',
    accountSettings: 'Account',
    subscriptionSettings: 'Subscription',
    theme: 'Theme',
    light: 'Light',
    dark: 'Dark',
    auto: 'Auto',

    // Model types
    modelSlowDescription: 'Economical, ideal for simple questions',
    modelMediumDescription: 'Balanced between speed and quality',
    modelFastDescription: 'Premium, best quality and speed',

    // Common
    loading: 'Loading...',
    error: 'Error',
    save: 'Save',
    cancel: 'Cancel',
    delete: 'Delete',
    edit: 'Edit',
    search: 'Search',
    close: 'Close',
    back: 'Back',
    next: 'Next',
    submit: 'Submit',
    confirm: 'Confirm',
  },
};

export const t = (key: keyof Translations, language: Language): string => {
  return translations[language][key];
};

export const useTranslation = (language: Language) => {
  return {
    t: (key: keyof Translations) => t(key, language),
    translations: translations[language],
  };
};

export default translations;
