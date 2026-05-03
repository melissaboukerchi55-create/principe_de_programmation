# LearnPy — SAE DDAW

> **SAE Sup-Galilée — Développement & Déploiement d'une Application Web RESTful Conteneurisée**

API REST pour une plateforme de cours en ligne (**React / Node.js / Django**) avec persistance PostgreSQL, ORM SQLAlchemy, conteneurisation Docker et orchestration Docker Compose.

---

## Sommaire

1. [Contexte & objectifs](#1-contexte--objectifs)
2. [Stack technique](#2-stack-technique)
3. [Architecture du projet](#3-architecture-du-projet)
4. [Modèle de données — les 3 relations exigées](#4-modèle-de-données--les-3-relations-exigées)
5. [Lancer l'application avec Docker Compose](#5-lancer-lapplication-avec-docker-compose)
6. [Comptes de test](#6-comptes-de-test)
7. [Exemples de routes REST](#7-exemples-de-routes-rest)
8. [Tests automatisés](#8-tests-automatisés)
9. [Image Docker Hub](#9-image-docker-hub)
10. [Choix techniques assumés](#10-choix-techniques-assumés)
11. [Auteurs](#11-auteurs)

---

## 1. Contexte & objectifs

LearnPy est une plateforme miniature qui permet à des **instructeurs** de publier des cours sur les frameworks web modernes (React, Node.js, Django), et à des **étudiants** de s'y inscrire, suivre leur progression et noter les cours suivis.

L'objectif pédagogique de cette SAE est de mettre en œuvre l'ensemble du cycle de vie logiciel : conception, développement, persistance via ORM, exposition d'une API REST, conteneurisation, et déploiement.

---

## 2. Stack technique

| Couche               | Technologie                                       |
| -------------------- | ------------------------------------------------- |
| Langage              | Python 3.12                                       |
| Framework Web        | FastAPI 0.115                                     |
| ORM                  | SQLAlchemy 2.0 (mapping déclaratif typé `Mapped`) |
| Validation / Schemas | Pydantic v2                                       |
| Base de données      | PostgreSQL 16                                     |
| Auth                 | JWT (PyJWT) + bcrypt                              |
| Tests                | pytest + httpx                                    |
| Conteneurisation     | Docker (multi-stage) + Docker Compose             |
| Documentation API    | Swagger UI auto sur `/docs` (OpenAPI 3.1)         |

---

## 3. Architecture du projet

```
ddaw-learnpy/
├── README.md
├── docker-compose.yml          ← orchestre api + db
├── .env.example                ← template d'environnement
├── backend/
│   ├── Dockerfile              ← image multi-stage, utilisateur non-root
│   ├── requirements.txt
│   └── app/
│       ├── main.py             ← entrypoint FastAPI (lifespan)
│       ├── core/
│       │   ├── config.py       ← settings via pydantic-settings
│       │   ├── database.py     ← engine + SessionLocal + retry au démarrage
│       │   ├── security.py     ← bcrypt + JWT + dépendances de rôle
│       │   └── seed.py         ← jeu de données idempotent
│       ├── models/             ← classes ORM (les 3 relations)
│       │   ├── user.py         ← User + Profile (1:1)
│       │   ├── category.py
│       │   ├── course.py       ← Course + Lesson (1:N)
│       │   └── enrollment.py   ← table M:N avec attributs
│       ├── schemas/            ← Pydantic In/Out
│       ├── routers/            ← endpoints REST par domaine
│       └── tests/              ← pytest (24 tests)
└── db/
    └── seed.sql                ← équivalent SQL du seed (alternatif)
```

**Vue logique** : 2 conteneurs orchestrés par Docker Compose, communiquant sur le réseau interne :

```
┌────────────────────┐         ┌─────────────────────┐
│   api (FastAPI)    │ ──────► │   db (Postgres 16)  │
│   :8000 → host     │   :5432 │   volume: pgdata    │
└────────────────────┘         └─────────────────────┘
        ▲
        │ HTTP REST + JWT
        │
   Postman / Swagger / curl
```

---

## 4. Modèle de données — les 3 relations exigées

Le sujet impose la modélisation des **trois** types de relations. Toutes sont présentes et **utilisées** par l'API :

| Relation        | Entités                              | Implémentation                                                                                                |
| --------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| **One-to-One**  | `User` ↔ `Profile`                   | FK `profile.user_id` **UNIQUE** + `relationship(uselist=False)` côté parent                                   |
| **One-to-Many** | `Category` → `Course`                | FK `course.category_id`                                                                                       |
| **One-to-Many** | `Course` → `Lesson`                  | FK `lesson.course_id` avec `cascade="all, delete-orphan"`                                                     |
| **One-to-Many** | `Instructor (User)` → `Course`       | FK `course.instructor_id`                                                                                     |
| **Many-to-Many**| `Student (User)` ↔ `Course`          | Classe d'association `Enrollment` (PK composite + colonnes `enrolled_at`, `progress`, `rating`)               |

### Schéma simplifié

```
users (id, email, full_name, role, hashed_password, created_at)
  └─1:1─ profiles (id, user_id UNIQUE→users.id, bio, avatar_url, github_url)

categories (id, name UNIQUE, slug, description)
  └─1:N─ courses

courses (id, title, description, category_id→categories.id, instructor_id→users.id,
         published, created_at)
  ├─1:N─ lessons (id, course_id→courses.id, title, content, position, duration_min)
  └─N:M─ enrollments (
            student_id  →users.id   ┐ PK composite
            course_id   →courses.id ┘
            enrolled_at, progress (0–100), rating (1–5 ou NULL)
         )
```

### Contraintes en base

- `progress BETWEEN 0 AND 100`
- `rating IS NULL OR rating BETWEEN 1 AND 5`
- `(student_id, course_id)` clé primaire composite → unicité d'inscription
- Cascades : suppression d'un cours → suppression de ses leçons et inscriptions

---

## 5. Lancer l'application avec Docker Compose

### Prérequis

- Docker ≥ 24
- Docker Compose v2

### Démarrage

```bash
# 1. Cloner le dépôt
git clone <url-du-depot>
cd ddaw-learnpy

# 2. Préparer l'environnement
cp .env.example .env
# (éditer .env si besoin pour changer JWT_SECRET en production)

# 3. Build + démarrage
docker compose up --build
```

Lancez cette commande depuis `ddaw-learnpy/`, pas depuis `ddaw-learnpy/backend/`. Si vous êtes déjà dans `backend/`, revenez d'abord au dossier parent avec `cd ..`.

Par défaut, l'API est exposée sur le port `8001` afin d'éviter les conflits avec un autre service déjà lancé sur `8000`. Vous pouvez changer ce port avec `API_PORT` dans `.env`.

L'API est ensuite disponible :

| URL                                   | Description                          |
| ------------------------------------- | ------------------------------------ |
| <http://localhost:8001/>              | Page racine                          |
| <http://localhost:8001/health>        | Liveness probe                       |
| <http://localhost:8001/docs>          | **Swagger UI** (interactif)          |
| <http://localhost:8001/redoc>         | ReDoc (lecture seule)                |
| <http://localhost:8001/api/v1/...>    | Endpoints REST                       |

Au premier démarrage, le **jeu de données de démo se charge automatiquement** (3 catégories, 2 instructeurs, 3 étudiants, 4 cours, 5 inscriptions). C'est idempotent : redémarrer ne re-seed pas.

### Réinitialiser la base

```bash
docker compose down -v   # -v supprime aussi le volume pgdata
docker compose up --build
```

### Charger le seed SQL alternatif

Si vous préférez utiliser `db/seed.sql` directement (par exemple pour une démo sans démarrer l'API) :

```bash
docker compose up -d db
docker compose exec -T db psql -U learnpy -d learnpy < db/seed.sql
```

---

## 6. Comptes de test

Tous les comptes ont le mot de passe **`demo1234`**.

| Rôle       | Email                  |
| ---------- | ---------------------- |
| Instructor | `alice@learnpy.dev`    |
| Instructor | `karim@learnpy.dev`    |
| Student    | `bob@learnpy.dev`      |
| Student    | `chloe@learnpy.dev`    |
| Student    | `dimitri@learnpy.dev`  |

---

## 7. Exemples de routes REST

Préfixe : tous les endpoints sont sous `/api/v1`. Conventions HTTP standards (200, 201, 204, 400, 401, 403, 404, 409, 422).

### 7.1 Authentification

**Inscription** :

```bash
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "supersecret1",
    "full_name": "New User",
    "role": "student"
  }'
```

**Connexion** (retourne le JWT à utiliser dans `Authorization: Bearer <token>`) :

```bash
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "bob@learnpy.dev", "password": "demo1234"}'
```

Réponse :

```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": { "id": 3, "email": "bob@learnpy.dev", "role": "student", ... }
}
```

### 7.2 Catégories (1:N côté parent)

```bash
# Liste
curl http://localhost:8001/api/v1/categories

# Détail
curl http://localhost:8001/api/v1/categories/1

# Création (instructor only)
curl -X POST http://localhost:8001/api/v1/categories \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Vue.js", "slug": "vuejs", "description": "Vue framework"}'
```

### 7.3 Cours (1:N + relations) — toutes les méthodes HTTP

```bash
# Liste paginée + filtres
curl "http://localhost:8001/api/v1/courses?category_id=1&published_only=true&limit=10"

# Détail (inclut les leçons triées + l'instructeur + la catégorie)
curl http://localhost:8001/api/v1/courses/1

# Création (POST)
curl -X POST http://localhost:8001/api/v1/courses \
  -H "Authorization: Bearer $INSTRUCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "React Hooks Deep Dive",
    "description": "All about hooks",
    "category_id": 1,
    "published": false
  }'

# Remplacement complet (PUT) — propriétaire uniquement
curl -X PUT http://localhost:8001/api/v1/courses/5 \
  -H "Authorization: Bearer $INSTRUCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Updated","description":"New desc","category_id":1,"published":true}'

# Mise à jour partielle (PATCH) — pratique pour publier/dépublier
curl -X PATCH http://localhost:8001/api/v1/courses/5 \
  -H "Authorization: Bearer $INSTRUCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"published": true}'

# Suppression (DELETE) — cascade vers leçons et inscriptions
curl -X DELETE http://localhost:8001/api/v1/courses/5 \
  -H "Authorization: Bearer $INSTRUCTOR_TOKEN"
```

### 7.4 Leçons (1:N côté enfant)

```bash
# Liste des leçons d'un cours (triées par position)
curl http://localhost:8001/api/v1/courses/1/lessons

# Ajout d'une leçon
curl -X POST http://localhost:8001/api/v1/courses/1/lessons \
  -H "Authorization: Bearer $INSTRUCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"useEffect","content":"...","position":4,"duration_min":35}'
```

### 7.5 Inscriptions (Many-to-Many avec attributs)

```bash
# S'inscrire (student only)
curl -X POST http://localhost:8001/api/v1/courses/1/enroll \
  -H "Authorization: Bearer $STUDENT_TOKEN"

# Mettre à jour sa progression et donner une note
curl -X PATCH http://localhost:8001/api/v1/courses/1/enroll \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"progress": 75, "rating": 5}'

# Se désinscrire
curl -X DELETE http://localhost:8001/api/v1/courses/1/enroll \
  -H "Authorization: Bearer $STUDENT_TOKEN"

# Lister mes inscriptions (cours suivis avec progression)
curl http://localhost:8001/api/v1/users/me/enrollments \
  -H "Authorization: Bearer $STUDENT_TOKEN"

# Lister les étudiants d'un cours (instructeur du cours)
curl http://localhost:8001/api/v1/courses/1/students \
  -H "Authorization: Bearer $INSTRUCTOR_TOKEN"
```

### 7.6 Profil (1:1)

```bash
# Mon profil
curl http://localhost:8001/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"

# Mettre à jour son profil
curl -X PUT http://localhost:8001/api/v1/users/me/profile \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"bio":"Passionate learner", "github_url":"https://github.com/me"}'
```

### Récapitulatif des méthodes HTTP utilisées

| Méthode  | Exemples                                                                          |
| -------- | --------------------------------------------------------------------------------- |
| `GET`    | `/courses`, `/courses/{id}`, `/users/me`, `/categories`, `/users/me/enrollments`  |
| `POST`   | `/auth/register`, `/auth/login`, `/courses`, `/courses/{id}/lessons`, `/.../enroll` |
| `PUT`    | `/courses/{id}`, `/lessons/{id}`, `/users/me/profile`                             |
| `PATCH`  | `/courses/{id}`, `/courses/{id}/enroll`                                           |
| `DELETE` | `/courses/{id}`, `/lessons/{id}`, `/.../enroll`, `/categories/{id}`               |

✅ Conformité totale au sujet (GET / POST / PUT / PATCH / DELETE).

---

## 8. Tests automatisés

24 tests pytest couvrant authentification, autorisation, CRUD, cascades, contraintes et les trois relations.

```bash
# Depuis le dossier backend/, dans un venv local :
pip install -r requirements.txt
python -m pytest app/tests/ -v
```

Sortie attendue : `24 passed`.

Les tests utilisent SQLite en mémoire pour rester rapides et hermétiques (pas de besoin Postgres).

---

## 9. Image Docker Hub

### Lien public

`https://hub.docker.com/r/melissaboukerchi/learnpy-api`

### Build & push (à faire une fois)

```bash
docker login

cd backend
docker build -t melissaboukerchi/learnpy-api:1.0.0 -t melissaboukerchi/learnpy-api:latest .
docker push melissaboukerchi/learnpy-api:1.0.0
docker push melissaboukerchi/learnpy-api:latest
```

### Lancer l'image depuis Docker Hub (sans cloner le repo)

```bash
# 1. Démarrer une base Postgres
docker run -d --name learnpy-db \
  -e POSTGRES_USER=learnpy -e POSTGRES_PASSWORD=learnpy -e POSTGRES_DB=learnpy \
  -v learnpy-pgdata:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:16-alpine

# 2. Démarrer l'API
docker run -d --name learnpy-api \
  --link learnpy-db:db \
  -e POSTGRES_HOST=db -e POSTGRES_USER=learnpy \
  -e POSTGRES_PASSWORD=learnpy -e POSTGRES_DB=learnpy \
  -e JWT_SECRET=change-me \
  -p 8001:8000 \
  melissaboukerchi/learnpy-api:latest
```

Le **volume nommé `learnpy-pgdata`** garantit la persistance entre redémarrages (cf. point bonus du sujet).

---

## 10. Choix techniques assumés

| Décision                                          | Raison                                                                                           |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `Base.metadata.create_all()` au démarrage         | Suffit pour la SAE — Alembic ajoute de l'overhead non demandé et le sujet n'exige pas de migrations versionnées. |
| Seed Python idempotent plutôt que `seed.sql` auto | Le seed Python s'exécute *après* la création des tables (faite par l'ORM), évitant la duplication DDL. Le SQL est fourni en complément. |
| `bcrypt` direct (sans passlib)                    | Passlib 1.7.4 a un bug avec bcrypt ≥ 4.1. Appel direct = moins de couches, comportement clair.   |
| JWT plutôt que sessions                           | Stateless, plus simple à containeriser et à présenter en démo (pas besoin de Redis).             |
| FastAPI `lifespan` plutôt que `on_event`          | API moderne (recommandée par FastAPI ≥ 0.93), pas de DeprecationWarning.                         |
| Classe d'association `Enrollment` (pas `secondary`)| Permet de stocker `progress` et `rating` directement sur la relation N:M.                        |
| `pool_pre_ping=True` + retry au démarrage         | Évite les déconnexions silencieuses et la race condition api/db sur Compose.                     |
| Healthcheck `pg_isready` côté Postgres            | `depends_on: condition: service_healthy` retarde le démarrage de l'API jusqu'à ce que la BDD réponde. |
| Image Docker multi-stage + utilisateur non-root   | Image finale plus petite (~150 MB) et bonne pratique sécurité.                                   |

---

## 11. Auteurs

Projet réalisé par boukerchi melissa et youdihat yamina — Sup-Galilée — promo 2025-2026.

