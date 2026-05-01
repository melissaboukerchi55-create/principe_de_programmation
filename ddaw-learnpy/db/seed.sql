-- ============================================================================
-- LearnPy — Demo seed (raw SQL version)
-- ============================================================================
-- This SQL is equivalent to the Python seed in app/core/seed.py.
-- It is provided to satisfy the SAE requirement of a SQL import file.
--
-- USAGE — to load this manually into a running Postgres instance:
--   docker exec -i learnpy-db psql -U learnpy -d learnpy < db/seed.sql
--
-- NOTE — by default the application auto-seeds itself on first start through
-- app/core/seed.py, so you typically do NOT need to run this file. Use it only
-- if you want to reset or load data outside the app's startup hook.
-- The schema (CREATE TABLE …) is created by SQLAlchemy from the ORM models,
-- not by this file — keeps a single source of truth for the data model.
-- ============================================================================

-- IMPORTANT: passwords here are bcrypt hashes of "demo1234".
-- They must match what the API generates with hash_password("demo1234").
-- Re-generate with:
--   python -c "import bcrypt; print(bcrypt.hashpw(b'demo1234', bcrypt.gensalt(rounds=12)).decode())"

BEGIN;

-- Clean slate (safe because of CASCADE)
TRUNCATE enrollments, lessons, courses, profiles, categories, users RESTART IDENTITY CASCADE;

-- --- Categories (3) ---
INSERT INTO categories (name, slug, description) VALUES
  ('React',   'react',  'Modern UI development with React'),
  ('Node.js', 'nodejs', 'Server-side JavaScript with Node.js'),
  ('Django',  'django', 'Python web framework — batteries included');

-- --- Users (2 instructors + 3 students) ---
-- The bcrypt hash below is for "demo1234". Generated with rounds=12.
INSERT INTO users (email, full_name, role, hashed_password) VALUES
  ('alice@learnpy.dev',   'Alice Martin',   'instructor', '$2b$12$LIbmCh4eFW2dYg.ws8AmKuq2bYBpVQZBjF4gxDNJYK7KcU4lXvT3K'),
  ('karim@learnpy.dev',   'Karim Benali',   'instructor', '$2b$12$LIbmCh4eFW2dYg.ws8AmKuq2bYBpVQZBjF4gxDNJYK7KcU4lXvT3K'),
  ('bob@learnpy.dev',     'Bob Dupont',     'student',    '$2b$12$LIbmCh4eFW2dYg.ws8AmKuq2bYBpVQZBjF4gxDNJYK7KcU4lXvT3K'),
  ('chloe@learnpy.dev',   'Chloé Petit',    'student',    '$2b$12$LIbmCh4eFW2dYg.ws8AmKuq2bYBpVQZBjF4gxDNJYK7KcU4lXvT3K'),
  ('dimitri@learnpy.dev', 'Dimitri Volkov', 'student',    '$2b$12$LIbmCh4eFW2dYg.ws8AmKuq2bYBpVQZBjF4gxDNJYK7KcU4lXvT3K');

-- --- Profiles (1:1 with users) ---
INSERT INTO profiles (user_id, bio, github_url) VALUES
  (1, 'Senior React engineer.',                  'https://github.com/alice'),
  (2, 'Backend specialist (Node + Django).',     'https://github.com/karim'),
  (3, 'CS student, eager to learn the stack.',   NULL),
  (4, 'Junior dev pivoting from Java to Python.', NULL),
  (5, NULL,                                       NULL);

-- --- Courses (4) ---
INSERT INTO courses (title, description, category_id, instructor_id, published) VALUES
  ('React Basics',                  'Foundations: components, JSX, state, hooks.', 1, 1, TRUE),
  ('Advanced React Patterns',       'Hooks, context, performance, code-splitting.', 1, 1, TRUE),
  ('Building REST APIs with Node.js','Express, async patterns, middlewares, testing.', 2, 2, TRUE),
  ('Django from Zero',              'Models, views, templates, admin, ORM.',      3, 2, FALSE);

-- --- Lessons (1:N from course) ---
INSERT INTO lessons (course_id, title, content, position, duration_min) VALUES
  (1, 'Introduction to React',     'What is React, virtual DOM',            1, 20),
  (1, 'JSX & components',          'Composing your first components',       2, 35),
  (1, 'State and useState',        'Managing local state',                  3, 40),
  (2, 'Custom hooks',              '',                                      1, 45),
  (2, 'Context API',               '',                                      2, 30),
  (3, 'Setting up Express',        '',                                      1, 25),
  (3, 'Routing & middlewares',     '',                                      2, 35),
  (3, 'Persistence with an ORM',   '',                                      3, 50),
  (4, 'Project layout',            '',                                      1, 20),
  (4, 'The ORM',                   '',                                      2, 40);

-- --- Enrollments (M:N with attributes: progress + rating) ---
INSERT INTO enrollments (student_id, course_id, progress, rating) VALUES
  (3, 1, 80,  5),
  (3, 3, 30,  NULL),
  (4, 4, 50,  4),
  (4, 1, 10,  NULL),
  (5, 2, 100, 5);

COMMIT;
