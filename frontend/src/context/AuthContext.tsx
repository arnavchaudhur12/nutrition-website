import { createContext, useContext, useEffect, useState } from "react";

type AuthUser = {
  email: string;
  fullName: string;
  initial: string;
  isAdmin: boolean;
};

type AuthContextValue = {
  user: AuthUser | null;
  loginUser: (user: AuthUser) => void;
  logoutUser: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const USER_STORAGE_KEY = "lagads-auth-user";

function getInitialFromEmail(email: string): string {
  return email.trim().charAt(0).toUpperCase() || "U";
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem(USER_STORAGE_KEY);
    if (!stored) {
      return;
    }

    try {
      setUser(JSON.parse(stored) as AuthUser);
    } catch {
      localStorage.removeItem(USER_STORAGE_KEY);
    }
  }, []);

  const loginUser = (nextUser: AuthUser) => {
    setUser(nextUser);
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(nextUser));
  };

  const logoutUser = () => {
    setUser(null);
    localStorage.removeItem(USER_STORAGE_KEY);
    localStorage.removeItem("lagads-user-token");
    localStorage.removeItem("lagads-admin-token");
  };

  return (
    <AuthContext.Provider value={{ user, loginUser, logoutUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}

export function buildAuthUser(email: string, fullName: string, isAdmin: boolean): AuthUser {
  return {
    email,
    fullName,
    initial: getInitialFromEmail(email),
    isAdmin
  };
}
