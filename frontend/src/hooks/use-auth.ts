import { useEffect } from "react";
import { useAuthStore } from "../stores/auth-store";

export function useAuth() {
  const auth = useAuthStore();

  useEffect(() => {
    auth.initialize();
  }, []);

  return auth;
}
