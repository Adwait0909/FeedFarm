# Demonstration accounts

The archive's database started with three sample cows. The included seed
command fills it to 100 cows, creates 10 demo farmers and 10 veterinarian
profiles, and adds six synthetic medical-history entries per cow. Each doctor
is linked to 60 distinct cow profiles through the medical-history table.

Run `python scripts/seed_demo_data.py` after installing `requirements.txt`.
The seed is repeatable and keeps existing records. It refuses to report success
if the resulting cow total is not exactly 100.

## Farmer sign-in

All 10 seeded farmer accounts use the suffix `@demo.example.test` and the same
demo password: `FarmDemo@2026`.

| Farmer | Email |
|---|---|
| Ramesh Patil | `ramesh.patil@demo.example.test` |
| Sunita Patil | `sunita.patil@demo.example.test` |
| Vijay Jadhav | `vijay.jadhav@demo.example.test` |
| Meera Shinde | `meera.shinde@demo.example.test` |
| Ganesh More | `ganesh.more@demo.example.test` |
| Kavita Pawar | `kavita.pawar@demo.example.test` |
| Nitin Deshmukh | `nitin.deshmukh@demo.example.test` |
| Anita Bhosale | `anita.bhosale@demo.example.test` |
| Suresh Chavan | `suresh.chavan@demo.example.test` |
| Lata Gawade | `lata.gawade@demo.example.test` |

## Veterinarian sign-in

The 10 seeded doctor profiles get a random password that the seed script prints once
(or the value of `DEMO_DOCTOR_PASSWORD` if you set it). Doctor accounts that already existed
keep their current password. In the database shipped with this project all 10 doctor accounts were switched to "no password set"; `python scripts/reset_doctor_passwords.py` (run by setup) gives each a new random password. Older copies of this project used the published password
`Vet@2026`; such accounts are blocked from signing in unless `FARM2FEED_DEMO_MODE=1`
is set, and `python scripts/reset_doctor_passwords.py` replaces those passwords.
The original account is `doctor@farmcare.local`; the remaining nine accounts
are listed in the doctors table and veterinary directory.

All farmer names, contact numbers, health entries, and profiles created by this
seed script are synthetic demonstration data, not real identities, patient
records, or medical advice. Set `DEMO_FARMER_PASSWORD` and
`DEMO_DOCTOR_PASSWORD` before seeding a shared demo environment. Do not use
the demonstration credentials on a public or production deployment.
