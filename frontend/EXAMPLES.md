# Exemples Pratiques d'Utilisation des Composants Accessibles

## 1. Créer un Formulaire de Connexion

```tsx
'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Mail, Lock } from 'lucide-react';

export function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Valider et soumettre
      if (!email.includes('@')) {
        setError('Email invalide');
        return;
      }

      // API call...

    } catch (err) {
      setError('Erreur de connexion');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h1>Connexion</h1>

      {/* Alerte d'erreur */}
      {error && (
        <div
          role="alert"
          aria-live="assertive"
          className="p-4 bg-red-100 text-red-800 rounded"
        >
          {error}
        </div>
      )}

      {/* Email Input */}
      <div className="space-y-2">
        <label htmlFor="login-email">Adresse email</label>
        <Input
          id="login-email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          leftIcon={<Mail className="w-5 h-5" />}
          placeholder="user@example.com"
          required
          ariaLabel="Adresse email"
        />
      </div>

      {/* Password Input */}
      <div className="space-y-2">
        <label htmlFor="login-password">Mot de passe</label>
        <Input
          id="login-password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          leftIcon={<Lock className="w-5 h-5" />}
          placeholder="••••••••"
          required
          ariaLabel="Mot de passe"
        />
      </div>

      {/* Submit Button */}
      <Button type="submit" className="w-full" loading={loading}>
        Se connecter
      </Button>
    </form>
  );
}
```

## 2. Créer une Modal Accessible

```tsx
'use client';

import { useState } from 'react';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export function EditProfileModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [name, setName] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Soumettre les données
    setIsOpen(false);
  };

  return (
    <>
      {/* Bouton qui ouvre la modal */}
      <Button onClick={() => setIsOpen(true)}>
        Modifier le profil
      </Button>

      {/* Modal Accessible */}
      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Modifier votre profil"
        size="md"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="edit-name">Nom complet</label>
            <Input
              id="edit-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="John Doe"
              required
            />
          </div>

          <div className="flex gap-2 justify-end">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsOpen(false)}
            >
              Annuler
            </Button>
            <Button type="submit" variant="primary">
              Enregistrer
            </Button>
          </div>
        </form>
      </Modal>
    </>
  );
}
```

## 3. Créer une Liste avec Boutons Icon-Only

```tsx
'use client';

import { Button } from '@/components/ui/button';
import { Trash2, Edit2, Share2 } from 'lucide-react';

interface Item {
  id: string;
  name: string;
}

export function ItemList({ items }: { items: Item[] }) {
  return (
    <div className="space-y-2">
      <h2>Articles</h2>
      <ul className="space-y-2">
        {items.map((item) => (
          <li
            key={item.id}
            className="flex items-center justify-between p-4 border rounded"
          >
            <span>{item.name}</span>

            {/* Boutons Icon-Only avec aria-label */}
            <div className="flex gap-2">
              <Button
                size="icon"
                iconOnly
                variant="ghost"
                ariaLabel={`Partager ${item.name}`}
              >
                <Share2 className="w-4 h-4" />
              </Button>

              <Button
                size="icon"
                iconOnly
                variant="ghost"
                ariaLabel={`Éditer ${item.name}`}
              >
                <Edit2 className="w-4 h-4" />
              </Button>

              <Button
                size="icon"
                iconOnly
                variant="danger"
                ariaLabel={`Supprimer ${item.name}`}
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

## 4. Créer un Formulaire avec Validation

```tsx
'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

export function RegistrationForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');

  const handlePasswordChange = (value: string) => {
    setPassword(value);

    // Validation en temps réel
    if (value && value.length < 8) {
      setPasswordError('Minimum 8 caractères');
    } else if (value) {
      setPasswordError('');
    }
  };

  return (
    <form className="space-y-4">
      <h1>Créer un compte</h1>

      {/* Email */}
      <div>
        <label htmlFor="reg-email">Email</label>
        <Input
          id="reg-email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>

      {/* Password avec validation */}
      <div>
        <label htmlFor="reg-password">Mot de passe</label>
        <Input
          id="reg-password"
          type="password"
          value={password}
          onChange={(e) => handlePasswordChange(e.target.value)}
          error={!!passwordError && password !== ''}
          errorMessage={passwordError}
          ariaDescribedBy="password-requirements"
          required
        />
        <p id="password-requirements" className="text-sm text-gray-600 mt-1">
          Au minimum 8 caractères avec majuscules et chiffres.
        </p>
      </div>

      <Button type="submit" className="w-full">
        S'inscrire
      </Button>
    </form>
  );
}
```

## 5. Créer une Toolbar avec Boutons

```tsx
'use client';

import { Button } from '@/components/ui/button';
import {
  Save,
  Trash2,
  Copy,
  Download,
  Settings,
} from 'lucide-react';

export function DocumentToolbar() {
  return (
    <div className="flex gap-2 p-4 border-b" role="toolbar" aria-label="Document actions">
      {/* Bouton avec icône et texte */}
      <Button
        size="sm"
        leftIcon={<Save className="w-4 h-4" />}
      >
        Enregistrer
      </Button>

      {/* Séparateur */}
      <div className="w-px bg-gray-200" />

      {/* Boutons icon-only groupés */}
      <div className="flex gap-1">
        <Button
          size="icon-sm"
          variant="ghost"
          iconOnly
          ariaLabel="Copier le document"
        >
          <Copy className="w-4 h-4" />
        </Button>

        <Button
          size="icon-sm"
          variant="ghost"
          iconOnly
          ariaLabel="Télécharger le document"
        >
          <Download className="w-4 h-4" />
        </Button>

        <Button
          size="icon-sm"
          variant="ghost"
          iconOnly
          ariaLabel="Paramètres du document"
        >
          <Settings className="w-4 h-4" />
        </Button>
      </div>

      {/* Bouton de suppression */}
      <Button
        size="icon-sm"
        variant="danger"
        iconOnly
        ariaLabel="Supprimer le document"
        className="ml-auto"
      >
        <Trash2 className="w-4 h-4" />
      </Button>
    </div>
  );
}
```

## 6. Créer une Recherche Accessible

```tsx
'use client';

import { useState } from 'react';
import { SearchInput } from '@/components/ui/input';

export function SearchBar() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<string[]>([]);

  const handleSearch = (value: string) => {
    setQuery(value);

    // Rechercher et afficher les résultats
    if (value.length > 2) {
      // API call...
      setResults(['Résultat 1', 'Résultat 2']);
    }
  };

  const handleClear = () => {
    setQuery('');
    setResults([]);
  };

  return (
    <div className="space-y-4">
      {/* Recherche avec label pour accessibilité */}
      <label htmlFor="search-bar" className="sr-only">
        Rechercher
      </label>
      <SearchInput
        id="search-bar"
        value={query}
        onChange={(e) => handleSearch(e.target.value)}
        onClear={handleClear}
        placeholder="Rechercher..."
        aria-label="Rechercher des articles"
        aria-describedby="search-results-count"
      />

      {/* Résultats accessibles */}
      {results.length > 0 && (
        <div
          id="search-results-count"
          role="status"
          aria-live="polite"
          aria-atomic="true"
        >
          <p className="text-sm text-gray-600">
            {results.length} résultats trouvés
          </p>

          <ul className="space-y-2">
            {results.map((result, index) => (
              <li key={index} className="p-2 border rounded hover:bg-gray-100">
                {result}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

## 7. Utiliser l'ErrorBoundary

```tsx
// app/layout.tsx
import { ErrorBoundary } from '@/components/ErrorBoundary';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </body>
    </html>
  );
}

// Ou pour une section spécifique
export function DashboardSection() {
  return (
    <ErrorBoundary>
      <YourComplexComponent />
    </ErrorBoundary>
  );
}
```

## 8. Créer une Modale de Confirmation

```tsx
'use client';

import { useState } from 'react';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { AlertTriangle } from 'lucide-react';

export function DeleteConfirmationModal() {
  const [isOpen, setIsOpen] = useState(false);

  const handleDelete = () => {
    // Effectuer la suppression
    setIsOpen(false);
  };

  return (
    <>
      <Button
        variant="danger"
        onClick={() => setIsOpen(true)}
      >
        Supprimer
      </Button>

      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Confirmation de suppression"
        size="sm"
      >
        <div className="space-y-4">
          {/* Icône d'avertissement */}
          <div className="flex gap-3">
            <AlertTriangle
              className="w-6 h-6 text-red-500 flex-shrink-0"
              aria-hidden="true"
            />
            <div>
              <p className="font-semibold">Êtes-vous sûr ?</p>
              <p className="text-sm text-gray-600">
                Cette action ne peut pas être annulée.
              </p>
            </div>
          </div>

          {/* Boutons d'action */}
          <div className="flex gap-2 justify-end">
            <Button
              variant="secondary"
              onClick={() => setIsOpen(false)}
            >
              Annuler
            </Button>
            <Button
              variant="danger"
              onClick={handleDelete}
            >
              Supprimer
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
```

## Bonnes Pratiques à Retenir

### ✓ À Faire
- Toujours associer labels avec `htmlFor`
- Toujours ajouter `ariaLabel` sur boutons icon-only
- Marquer icônes décoratives avec `aria-hidden="true"`
- Utiliser `role="alert"` pour messages d'erreur
- Générer IDs uniques pour inputs
- Tester avec clavier (Tab, Enter, Escape)

### ✗ À Éviter
- Ne pas utiliser div/span pour inputs
- Ne pas oublier aria-label sur boutons
- Ne pas créer de modales sans `role="dialog"`
- Ne pas surcharger avec `tabindex`
- Ne pas utiliser `position: absolute` pour masquer labels
- Ne pas oublier `htmlFor` sur labels

---

**Pour plus d'informations**, consultez:
- `ACCESSIBILITY_GUIDE.md`
- `IMPLEMENTATION_NOTES.md`
- `TESTING_ACCESSIBILITY.md`
