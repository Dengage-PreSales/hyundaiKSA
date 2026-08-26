-- Synthetic DMS seed for the Hyundai KSA remote-data showcase.
--
-- Applied verbatim as migration hyundai_demo_dms_seed. Insert-only. Every
-- value is invented and announces itself as invented: DEMO- VINs, a 555
-- mobile block, DPS- contact keys. setseed makes the generated block
-- reproducible.
--
-- Eight presenter-typeable contacts come first, engineered so specific
-- segment demos land:
--   DPS-1  Tucson owner in Jeddah, warranty expiring inside 60 days
--   DPS-2  Accent owner, service overdue by more than 6 months
--   DPS-3  Palisade owner, high lifetime value
--   DPS-4  Santa Fe owner, service due next month

insert into public.hy_customer_vehicle
  (contact_key, full_name, mobile, city, model_id, model_name, trim, vin,
   purchase_date, warranty_end, last_service_date, next_service_due,
   odometer_km, service_center, lifetime_value_sar)
values
  ('DPS-1', 'Fahad Al-Ghamdi',  '+96650555001', 'Jeddah',  'tucson',    'TUCSON',    'Premium',     'DEMOTUCSON00001', date '2021-10-10', date '2026-10-10', date '2026-03-02', date '2026-09-02', 96400, 'Jeddah - Madinah Road SC', 6200),
  ('DPS-2', 'Noura Al-Harbi',   '+96653555002', 'Makkah',  'accent',    'ACCENT',    'Standard',    'DEMOACCENT00002', date '2022-05-18', date '2027-05-18', date '2025-11-09', date '2026-05-08', 78100, 'Makkah SC', 980),
  ('DPS-3', 'Khalid Al-Otaibi', '+96654555003', 'Jeddah',  'palisade',  'PALISADE',  'Calligraphy', 'DEMOPALISA00003', date '2023-02-04', date '2028-02-04', date '2026-06-14', date '2026-12-11', 61200, 'Jeddah - Sari Street SC', 18400),
  ('DPS-4', 'Reem Al-Zahrani',  '+96656555004', 'Madinah', 'santa-fe',  'SANTA FE',  'GL Premium',  'DEMOSANTAF00004', date '2024-07-21', date '2029-07-21', date '2026-03-23', date '2026-09-23', 38900, 'Madinah SC', 2600),
  ('DPS-5', 'Turki Al-Mutairi', '+96651555005', 'Jeddah',  'elantra',   'ELANTRA',   'Standard',    'DEMOELANTR00005', date '2023-09-12', date '2028-09-12', date '2026-05-30', date '2026-11-26', 52300, 'Jeddah - Madinah Road SC', 1400),
  ('DPS-6', 'Sara Bukhari',     '+96650555006', 'Taif',    'creta',     'CRETA',     'Standard',    'DEMOCRETA000006', date '2025-01-08', date '2030-01-08', date '2026-07-04', date '2027-01-01', 21800, 'Taif SC', 420),
  ('DPS-7', 'Majed Al-Shehri',  '+96653555007', 'Tabuk',   'sonata',    'SONATA',    'Standard',    'DEMOSONATA00007', date '2020-12-02', date '2025-12-02', date '2026-01-19', date '2026-07-18', 131500, 'Tabuk SC', 5200),
  ('DPS-8', 'Lama Al-Amri',     '+96656555008', 'Jeddah',  'venue',     'VENUE',     'Standard',    'DEMOVENUE000008', date '2025-06-15', date '2030-06-15', date '2026-08-02', date '2027-01-29', 9800,  'Jeddah - Sari Street SC', 0);

-- 292 generated owners on top of the eight engineered ones. random() is
-- called in the select list of a CTE so it is evaluated PER ROW: the first
-- version drew each value once inside uncorrelated laterals, and Postgres
-- runs those once for the whole query, which gave 292 owners one shared
-- purchase date.
select setseed(0.42);
with base as (
  select n,
         random() as r_purchase, random() as r_last, random() as r_city,
         random() as r_model, random() as r_trim, random() as r_first,
         random() as r_last_name, random() as r_prefix, random() as r_odo,
         random() as r_ltv, random() as r_center
  from generate_series(1, 292) as n
), shaped as (
  select n,
    date '2026-08-26' - (120 + floor(r_purchase * 2280))::int as purchase_date,
    (40 + floor(r_last * 360))::int as last_gap,
    case
      when r_city < 0.45 then 'Jeddah' when r_city < 0.60 then 'Makkah'
      when r_city < 0.72 then 'Madinah' when r_city < 0.80 then 'Taif'
      when r_city < 0.86 then 'Tabuk' when r_city < 0.91 then 'Yanbu'
      when r_city < 0.96 then 'Abha' else 'Khamis Mushait' end as city,
    case
      when r_model < 0.22 then 'accent' when r_model < 0.40 then 'tucson'
      when r_model < 0.54 then 'elantra' when r_model < 0.64 then 'creta'
      when r_model < 0.73 then 'santa-fe' when r_model < 0.81 then 'sonata'
      when r_model < 0.87 then 'palisade' when r_model < 0.92 then 'venue'
      when r_model < 0.96 then 'grandi10' else 'stargazer' end as model_id,
    r_trim, r_first, r_last_name, r_prefix, r_odo, r_ltv, r_center
  from base
)
insert into public.hy_customer_vehicle
  (contact_key, full_name, mobile, city, model_id, model_name, trim, vin,
   purchase_date, warranty_end, last_service_date, next_service_due,
   odometer_km, service_center, lifetime_value_sar)
select
  'DPS-17' || lpad(n::text, 7, '0'),
  (array['Mohammed','Abdullah','Fahad','Khalid','Saud','Nawaf','Turki','Faisal',
         'Bandar','Majed','Sara','Noura','Reem','Lama','Aisha','Huda','Dana',
         'Jawaher','Amal','Layan'])[1 + floor(r_first * 20)::int]
    || ' ' ||
  (array['Al-Harbi','Al-Ghamdi','Al-Qahtani','Al-Zahrani','Al-Otaibi',
         'Al-Mutairi','Al-Shehri','Al-Amri','Al-Juhani','Al-Maliki','Al-Subhi',
         'Al-Rehaili','Bukhari','Khoja','Fallatah'])[1 + floor(r_last_name * 15)::int],
  '+9665' || (array['0','1','3','4','5','6'])[1 + floor(r_prefix * 6)::int]
          || '555' || lpad((n % 1000)::text, 3, '0'),
  city,
  model_id,
  case model_id
    when 'accent' then 'ACCENT' when 'tucson' then 'TUCSON'
    when 'elantra' then 'ELANTRA' when 'creta' then 'CRETA'
    when 'santa-fe' then 'SANTA FE' when 'sonata' then 'SONATA'
    when 'palisade' then 'PALISADE' when 'venue' then 'VENUE'
    when 'grandi10' then 'GRAND i10' else 'STARGAZER' end,
  case when model_id = 'tucson'
       then (array['Smart','Comfort','Premium','N Line'])[1 + floor(r_trim * 4)::int]
       when model_id = 'santa-fe'
       then (array['GL Smart','GL Comfort','GL Premium','Calligraphy'])[1 + floor(r_trim * 4)::int]
       else 'Standard' end,
  'DEMO' || upper(replace(model_id, '-', '')) || lpad((n + 100)::text, 5, '0'),
  purchase_date,
  purchase_date + interval '5 years',
  purchase_date + greatest(30, (date '2026-08-26' - purchase_date) - last_gap),
  purchase_date + greatest(30, (date '2026-08-26' - purchase_date) - last_gap) + 180,
  ((date '2026-08-26' - purchase_date) * (25 + r_odo * 50))::int,
  case when city = 'Jeddah'
       then (array['Jeddah - Madinah Road SC','Jeddah - Sari Street SC'])[1 + floor(r_center * 2)::int]
       else city || ' SC' end,
  (array[0, 0, 420, 980, 1400, 2600, 5200, 8400])[1 + floor(r_ltv * 8)::int]
from shaped;

-- Service history: one to four completed visits per vehicle. The visit rows
-- come from a per-row CTE for the same per-row-randomness reason as above.
with visits as (
  select v.vin, v.contact_key, v.purchase_date, v.service_center,
         k, random() as r_gap, random() as r_type, random() as r_amount
  from public.hy_customer_vehicle as v
  cross join generate_series(1, 4) as k
)
insert into public.hy_service_history
  (vin, contact_key, visit_date, service_center, service_type, amount_sar, status)
select
  vin, contact_key,
  purchase_date + (k * (150 + floor(r_gap * 110))::int),
  service_center,
  (array['10K service','20K service','40K service','60K service','Repair','Recall check'])[least(k, 4) + (case when r_type < 0.2 then 2 else 0 end)],
  case when least(k, 4) + (case when r_type < 0.2 then 2 else 0 end) = 6
       then 0 else round((300 + r_amount * 1900)::numeric, 2) end,
  'completed'
from visits
where purchase_date + (k * (150 + floor(r_gap * 110))::int) < date '2026-08-26'
  and r_gap > (k - 1) * 0.18;

insert into public.hy_branch (name, city, branch_type, lat, lng) values
  ('Hyundai Showroom - Madinah Road',           'Jeddah',  'showroom',      21.5433, 39.1728),
  ('Hyundai Showroom - Sari Street',            'Jeddah',  'showroom',      21.5810, 39.1620),
  ('Hyundai Service Center - Industrial Area',  'Jeddah',  'service',       21.4460, 39.2410),
  ('Hyundai Showroom - Makkah',                 'Makkah',  'showroom',      21.3891, 39.8579),
  ('Hyundai Service Center - Makkah',           'Makkah',  'service',       21.4010, 39.8300),
  ('Hyundai Showroom - Madinah',                'Madinah', 'showroom',      24.4686, 39.6142),
  ('Hyundai Showroom - Taif',                   'Taif',    'showroom',      21.2854, 40.4211),
  ('Hyundai Showroom - Tabuk',                  'Tabuk',   'showroom',      28.3835, 36.5662),
  ('Hyundai Showroom - Abha',                   'Abha',    'showroom',      18.2465, 42.5117),
  ('Hyundai Quick Service - Yanbu',             'Yanbu',   'quick_service', 24.0895, 38.0618);
