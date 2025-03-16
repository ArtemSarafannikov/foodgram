create table public.users
(
    id              serial
        primary key,
    email           varchar,
    username        varchar
        unique,
    first_name      varchar,
    last_name       varchar,
    hashed_password varchar,
    avatar          bytea
);

alter table public.users
    owner to postgres;

create unique index ix_users_email
    on public.users (email);

create index ix_users_id
    on public.users (id);

create table public.ingredients
(
    id               serial
        primary key,
    name             varchar,
    measurement_unit varchar
);

alter table public.ingredients
    owner to postgres;

create index ix_ingredients_name
    on public.ingredients (name);

create index ix_ingredients_id
    on public.ingredients (id);

create table public.tags
(
    id   serial
        primary key,
    name varchar,
    slug varchar
        unique
);

alter table public.tags
    owner to postgres;

create index ix_tags_name
    on public.tags (name);

create index ix_tags_id
    on public.tags (id);

create table public.user_subscriptions
(
    user_id   integer
        references public.users,
    author_id integer
        references public.users
);

alter table public.user_subscriptions
    owner to postgres;

create table public.recipes
(
    id           serial
        primary key,
    name         varchar,
    image        bytea,
    cooking_time integer,
    text         varchar,
    author_id    integer
        references public.users
);

alter table public.recipes
    owner to postgres;

create index ix_recipes_name
    on public.recipes (name);

create index ix_recipes_id
    on public.recipes (id);

create table public.recipe_ingredients
(
    id            serial
        primary key,
    recipe_id     integer
        references public.recipes,
    ingredient_id integer
        references public.ingredients,
    amount        integer
);

alter table public.recipe_ingredients
    owner to postgres;

create index ix_recipe_ingredients_id
    on public.recipe_ingredients (id);

create table public.recipe_tags
(
    recipe_id integer
        references public.recipes,
    tag_id    integer
        references public.tags
);

alter table public.recipe_tags
    owner to postgres;

create table public.favourite_recipes
(
    user_id   integer
        references public.users,
    recipe_id integer
        references public.recipes
);

alter table public.favourite_recipes
    owner to postgres;

create table public.shopping_cart
(
    user_id   integer
        references public.users,
    recipe_id integer
        references public.recipes
);

alter table public.shopping_cart
    owner to postgres;

