-- The synthetic Hyundai DMS tables for the remote-data showcase.
--
-- Create-only, namespaced hy_*, following the same pattern the rh_* tables
-- set for a previous pitch in this database. Nothing existing is touched.
-- RLS is enabled with no policies, matching the house style: the tables are
-- read through the Dengage remote-source connection and the service role,
-- never from a browser.
--
-- What each table is for on the call:
--   hy_customer_vehicle  the DMS ownership record: who owns what, warranty
--                        and service dates. Remote segments are built on it
--                        ("warranty expires inside 60 days", "service overdue",
--                        "Tucson owners in Jeddah", "high lifetime value").
--   hy_service_history   workshop visits, for the after-sales story.
--   hy_branch            branches with coordinates, for the geofence scene.

create table public.hy_customer_vehicle (
    id                  bigint generated always as identity primary key,
    contact_key         text not null,
    full_name           text not null,
    mobile              text not null,
    city                text not null,
    model_id            text not null,
    model_name          text not null,
    trim                text,
    vin                 text not null unique,
    purchase_date       date not null,
    warranty_end        date not null,
    last_service_date   date,
    next_service_due    date,
    odometer_km         integer,
    service_center      text,
    lifetime_value_sar  numeric(10,2) default 0,
    created_at          timestamptz not null default now()
);
comment on table public.hy_customer_vehicle is
    'Synthetic DMS ownership records for the Hyundai KSA demo. Every value is invented: DEMO- VINs, 555-block mobiles, DPS- contact keys. Joined to Dengage contacts on contact_key.';
create index hy_customer_vehicle_contact_key on public.hy_customer_vehicle (contact_key);
create index hy_customer_vehicle_warranty on public.hy_customer_vehicle (warranty_end);
create index hy_customer_vehicle_next_due on public.hy_customer_vehicle (next_service_due);
alter table public.hy_customer_vehicle enable row level security;

create table public.hy_service_history (
    id              bigint generated always as identity primary key,
    vin             text not null references public.hy_customer_vehicle (vin),
    contact_key     text not null,
    visit_date      date not null,
    service_center  text,
    service_type    text not null,
    amount_sar      numeric(10,2) default 0,
    status          text not null default 'completed',
    created_at      timestamptz not null default now()
);
comment on table public.hy_service_history is
    'Synthetic workshop visits for the Hyundai KSA demo, keyed to hy_customer_vehicle.';
create index hy_service_history_contact_key on public.hy_service_history (contact_key);
alter table public.hy_service_history enable row level security;

create table public.hy_branch (
    id           bigint generated always as identity primary key,
    name         text not null,
    city         text not null,
    branch_type  text not null,
    lat          double precision not null,
    lng          double precision not null
);
comment on table public.hy_branch is
    'Approximate branch locations for the Hyundai KSA demo geofence scene. Coordinates are city-level approximations, not real branch addresses.';
alter table public.hy_branch enable row level security;
