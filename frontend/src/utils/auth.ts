
// utils/auth.ts

interface LoginResponse {
    access_token: string;
    refresh_token: string;
    token_type: "bearer";
    user: {
        user_id: string;
        email: string;
        full_name: string;
        is_verified: boolean;
        is_active: boolean;
    };
}

interface RegisterResponse {
    user_id: string;
    email: string;
    first_name: string;
    last_name: string;
    is_verified: boolean;
    is_active: boolean;
}

interface RefreshResponse {
    access_token: string;
    token_type: "bearer";
}

export class AuthManager {
    private static isRefreshing = false;
    private static refreshPromise: Promise<string> | null = null;
    private static API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

    /**
     * Récupère le token d'accès actuel
     */
    static getAccessToken(): string | null {
        if (typeof window === 'undefined') return null;
        return localStorage.getItem('access_token');
    }

    /**
     * Vérifie si l'utilisateur est connecté
     */
    static isAuthenticated(): boolean {
        return !!this.getAccessToken();
    }

    /**
     * Récupère les informations de l'utilisateur
     */
    static getUser() {
        if (typeof window === 'undefined') return null;
        const userStr = localStorage.getItem('user');
        if (!userStr) return null;

        try {
            return JSON.parse(userStr);
        } catch (error) {
            console.error('Failed to parse user data:', error);
            localStorage.removeItem('user'); // Clean corrupted data
            return null;
        }
    }

    /**
     * Login
     */
    static async login(email: string, password: string): Promise<LoginResponse> {
        const response = await fetch(`${this.API_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
        });

        if (!response.ok) {
            const error = await response.json();

            // Gérer les erreurs de validation (422)
            if (Array.isArray(error.detail)) {
                const messages = error.detail.map((err: any) => {
                    const field = err.loc ? err.loc[err.loc.length - 1] : 'champ';
                    return `${field}: ${err.msg}`;
                }).join(', ');
                throw new Error(messages);
            }

            throw new Error(error.detail || 'Login failed');
        }

        const data = await response.json();

        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('user', JSON.stringify(data.user));

        return data;
    }

    /**
     * Register
     */
    static async register(email: string, password: string, fullName: string): Promise<RegisterResponse> {
        // Séparer le nom complet en first_name et last_name
        const nameParts = fullName.trim().split(' ');
        const firstName = nameParts[0] || '';
        const lastName = nameParts.slice(1).join(' ') || nameParts[0] || '';

        const response = await fetch(`${this.API_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email,
                password,
                first_name: firstName,
                last_name: lastName,
            }),
        });

        if (!response.ok) {
            const error = await response.json();

            // Gérer les erreurs de validation (422)
            if (Array.isArray(error.detail)) {
                const messages = error.detail.map((err: any) => {
                    const field = err.loc ? err.loc[err.loc.length - 1] : 'champ';
                    return `${field}: ${err.msg}`;
                }).join(', ');
                throw new Error(messages);
            }

            throw new Error(error.detail || 'Registration failed');
        }

        return await response.json();
    }

    /**
     * Rafraîchir le token
     */
    private static async refreshAccessToken(): Promise<string> {
        const refreshToken = localStorage.getItem('refresh_token');

        if (!refreshToken) {
            throw new Error('No refresh token available');
        }

        const response = await fetch(`${this.API_URL}/auth/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (!response.ok) {
            // Token invalide, rediriger vers login
            this.logout();
            if (typeof window !== 'undefined') {
                window.location.href = '/login';
            }
            throw new Error('Session expired');
        }

        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);

        return data.access_token;
    }

    /**
     * Effectue une requête authentifiée avec gestion automatique du refresh
     */
    static async authenticatedFetch(
        url: string,
        options: RequestInit = {}
    ): Promise<Response> {

        // Si l'URL est relative (commence par /), ajouter l'URL de l'API
        const fullUrl = url.startsWith('http') ? url : `${this.API_URL}${url}`;

        let token = this.getAccessToken();

        if (!token) {
            throw new Error('Not authenticated');
        }

        // Ajouter le token à la requête
        const headers = new Headers(options.headers);
        headers.set('Authorization', `Bearer ${token}`);

        let response = await fetch(fullUrl, {
            ...options,
            headers,
        });

        // Si 401, essayer de rafraîchir le token
        if (response.status === 401) {
            // Éviter les rafraîchissements multiples simultanés
            if (!this.isRefreshing) {
                this.isRefreshing = true;
                this.refreshPromise = this.refreshAccessToken()
                    .finally(() => {
                        this.isRefreshing = false;
                        this.refreshPromise = null;
                    });
            }

            // Attendre le rafraîchissement
            try {
                token = await this.refreshPromise!;

                // Réessayer la requête avec le nouveau token
                headers.set('Authorization', `Bearer ${token}`);
                response = await fetch(fullUrl, {
                    ...options,
                    headers,
                });
            } catch (error) {
                // Refresh échoué, rediriger vers login
                this.logout();
                if (typeof window !== 'undefined') {
                    window.location.href = '/login';
                }
                throw error;
            }
        }

        return response;
    }

    /**
     * Déconnexion
     */
    static async logout() {
        const accessToken = this.getAccessToken();

        if (accessToken) {
            try {
                await fetch(`${this.API_URL}/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,
                    },
                });
            } catch (error) {
                console.error('Logout error:', error);
            }
        }

        // Nettoyer le stockage local
        if (typeof window !== 'undefined') {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
        }
    }
}
