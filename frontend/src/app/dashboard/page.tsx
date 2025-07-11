"use client";

import { createClient } from "@/lib/supabase/client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

interface User {
  id: string;
  email: string;
  user_metadata: {
    full_name?: string;
    avatar_url?: string;
  };
}

export default function Dashboard() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const supabase = createClient();
  const router = useRouter();

  useEffect(() => {
    const getUser = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        router.push("/");
        return;
      }

      setUser(session.user as User);
      setLoading(false);
    };

    getUser();
  }, [supabase, router]);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    router.push("/");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Chargement...</div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <button
              onClick={handleSignOut}
              className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
            >
              Se déconnecter
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h2 className="text-lg font-semibold mb-3">Informations utilisateur</h2>
              <div className="space-y-2">
                <p><span className="font-medium">Email:</span> {user.email}</p>
                <p><span className="font-medium">Nom:</span> {user.user_metadata.full_name || "Non défini"}</p>
                <p><span className="font-medium">ID:</span> {user.id}</p>
              </div>
            </div>

            <div className="bg-blue-50 p-4 rounded-lg">
              <h2 className="text-lg font-semibold mb-3">Actions disponibles</h2>
              <div className="space-y-2">
                <button className="block w-full text-left px-3 py-2 bg-blue-100 hover:bg-blue-200 rounded">
                  Gérer les comptes sociaux
                </button>
                <button className="block w-full text-left px-3 py-2 bg-blue-100 hover:bg-blue-200 rounded">
                  Voir les analytics
                </button>
                <button className="block w-full text-left px-3 py-2 bg-blue-100 hover:bg-blue-200 rounded">
                  Programmer du contenu
                </button>
              </div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-yellow-50 rounded-lg">
            <h3 className="font-semibold text-yellow-800 mb-2">Token d&apos;accès (pour le backend)</h3>
            <p className="text-sm text-yellow-700">
              Ce token sera automatiquement envoyé dans les en-têtes des requêtes vers le backend Python.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
} 