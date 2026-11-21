# ChEMBL catalogue for Video 8

The frozen catalogue contains 95 ChEMBL 37 small-molecule parent structures. Its scope is structural sampling near the Video 7 training chemistry. The catalogue omits recorded human EGFR matches for target `CHEMBL203` in the frozen ChEMBL release. Evidence about measurements in other resources and other target mappings falls outside that scope. [ChEMBL target record](https://www.ebi.ac.uk/chembl/explore/target/CHEMBL203), [ChEMBL data web services](https://chembl.gitbook.io/chembl-interface-documentation/web-services/chembl-data-web-services)

Seventeen fixed seed structures span all 13 exact Video 7 scaffold-development groups. The smallest numeric ChEMBL molecule ID supplies one seed per group. A structure-only farthest-first Morgan comparison supplies four more from the largest group. The query uses ChEMBL's catalogue similarity at 45%, with a cap of 1,000 rows per seed. All returned hits fit within the cap. The earlier 60% pilot yielded two eligible structures, so we broadened the catalogue retrieval before any fitted model was opened or scored. The web-service similarity controls retrieval. Video 8 calculates its own Morgan applicability against the frozen training set. [Fixed catalogue plan](CATALOGUE_PLAN.json), [Pilot lock](pilot-60/LIBRARY_LOCK.json)

The exclusion index covers all 58,847 activity rows for this target over 59 pages, across all endpoints and assay types. The check uses recorded activity molecule IDs, parent IDs, standardized InChIKeys and their connectivity blocks. It also excludes identities and connectivity blocks from both Video 7 label cohorts. We retain connected records labelled as small-molecule parents whose ChEMBL Standard InChIKey matches the pinned RDKit calculation. We sort by numeric ChEMBL ID and keep one row per Standard InChIKey. [Activity request ledger](CHEMBL_ACTIVITY_REQUESTS.json), [Catalogue request ledger](CHEMBL_CATALOGUE_REQUESTS.json)

The queries returned 3,796 hits with 563 distinct ChEMBL IDs. The screening of records excluded 439 target molecule or parent IDs, 3 additional structure or connectivity matches, and 26 records outside the connected small-molecule parent scope. The 95 retained rows have only `compound_id`, `smiles` and `inchikey`. Their assay answers remain unknown within this workflow. The model weights, predicted potency and prediction interval played no part in constructing this catalogue. [Frozen library](../data/source/LIBRARY.json), [Membership lock and exclusions](LIBRARY_LOCK.json)

## Replay from retained responses

From `Playlists/ai-in-drug-discovery/8/revisions/r3-saved-model`, run:

```sh
sh ../../../7/revisions/r3-syllabus/code/run_qsar.sh research/freeze_library.py build
```

The command checks every request digest, the complete target pagination, the Video 7 cohort and seed-plan hashes, and the exact bytes of the frozen library and its membership lock. The original ChEMBL API pages are under `data/source/raw`. `research/download_chembl.py` records how the activities and catalogue pages were acquired. Live services can return a later ChEMBL release, so the offline replay uses the retained pages.

ChEMBL data are attributed to EMBL-EBI under CC BY-SA 3.0. [ChEMBL license and suggested attribution](https://chembl.gitbook.io/chembl-interface-documentation/frequently-asked-questions/general-questions#can-you-provide-more-details-on-licensing), [Zdrazil et al.](https://doi.org/10.1093/nar/gkad1004)
