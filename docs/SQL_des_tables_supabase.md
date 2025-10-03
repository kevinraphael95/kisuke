# 🗄️ SQL — Création des tables pour le bot

Copier-coller le code ci-dessous dans SQL Editor pour créer toutes les tables nécessaires. (c'est pas à jour)

---

## 1️⃣ Table `bot_lock`

```sql
CREATE TABLE public.bot_lock (
    id TEXT NOT NULL,
    instance_id TEXT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NULL DEFAULT now(),
    CONSTRAINT bot_lock_pkey PRIMARY KEY (id)
) TABLESPACE pg_default;
````

---

## 2️⃣ Table `bot_settings`

```sql
CREATE TABLE public.bot_settings (
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    CONSTRAINT bot_settings_pkey PRIMARY KEY (key)
) TABLESPACE pg_default;
```

---

## 3️⃣ Table `reiatsu`

```sql
CREATE TABLE public.reiatsu (
    user_id TEXT NOT NULL,
    username TEXT NOT NULL,
    points BIGINT NOT NULL,
    last_steal_attempt TIMESTAMP WITHOUT TIME ZONE NULL,
    steal_cd SMALLINT NULL,
    classe TEXT NULL DEFAULT 'Travailleur'::text,
    comp_cd TIMESTAMP WITH TIME ZONE NULL,
    bonus5 SMALLINT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    CONSTRAINT reiatsu2_pkey PRIMARY KEY (user_id)
) TABLESPACE pg_default;
```

---

## 4️⃣ Table `reiatsu_config`

```sql
CREATE TABLE public.reiatsu_config (
    guild_id TEXT NOT NULL,
    channel_id TEXT NULL,
    en_attente BOOLEAN NULL DEFAULT false,
    last_spawn_at TIMESTAMP WITH TIME ZONE NULL,
    spawn_message_id TEXT NULL,
    spawn_delay INTEGER NULL DEFAULT 1800,
    CONSTRAINT reiatsu_config_pkey PRIMARY KEY (guild_id)
) TABLESPACE pg_default;
```

---

## 5️⃣ Table `steam_keys`

```sql
CREATE TABLE public.steam_keys (
    id BIGSERIAL NOT NULL,
    game_name TEXT NOT NULL,
    steam_url TEXT NOT NULL,
    steam_key TEXT NOT NULL,
    CONSTRAINT steam_keys_pkey PRIMARY KEY (id)
) TABLESPACE pg_default;
```

---

## 6️⃣ Table `gardens`

```sql
CREATE TABLE public.gardens (
    user_id BIGINT NOT NULL,
    username TEXT NOT NULL,
    garden_grid JSONB NOT NULL DEFAULT '[
        "🌱🌱🌱🌱🌱🌱🌱🌱",
        "🌱🌱🌱🌱🌱🌱🌱🌱",
        "🌱🌱🌱🌱🌱🌱🌱🌱"
    ]'::jsonb,
    inventory JSONB NOT NULL DEFAULT '{
        "roses": 0,
        "tulipes": 0,
        "hibiscus": 0,
        "jacinthes": 0,
        "tournesols": 0,
        "paquerettes": 0
    }'::jsonb,
    last_fertilize TIMESTAMP WITH TIME ZONE NULL,
    potions JSONB NULL,
    armee TEXT NULL,
    argent INTEGER NULL DEFAULT 0,
    CONSTRAINT gardens_pkey PRIMARY KEY (user_id)
) TABLESPACE pg_default;
```

