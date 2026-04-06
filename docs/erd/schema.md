PK primary key
FK foreign key
IDX indexed
NEW added from offline-capture decision

User
internal only
idPK
uuid
display_name
varchar
emailIDX
varchar
unique
auth_provider
varchar
auth0 | google | apple
auth_provider_idIDX
varchar
bio
text
location_home
geometry
PostGIS point
avatar_url
varchar
role
enum
observer | curator | admin
created_at
timestamptz
updated_at
timestamptz

Group
multi-tenancy foundation
idPK
uuid
name
varchar
slugIDX
varchar
unique, url-safe
description
text
group_type
enum
class|team|org|campaign|open
owner_idFK
uuid
→ User
is_public
boolean
join_policy
enum
open | invite | approval
created_at
timestamptz
updated_at
timestamptz

GroupMembership
junction
idPK
uuid
group_idFKIDX
uuid
→ Group
user_idFKIDX
uuid
→ User
role
enum
member | moderator | admin
joined_at
timestamptz

Species
DwC: Taxon
idPK
uuid
common_name
varchar
scientific_nameIDX
varchar
unique
kingdom
varchar
phylum
varchar
class_name
varchar
class is reserved in Python
order_name
varchar
family
varchar
genus
varchar
inaturalist_id
varchar
gbif_id
varchar
ala_id
varchar
conservation_status
varchar
IUCN code
description
text
created_at
timestamptz

Sighting
DwC: Occurrence
idPK
uuid
user_idFKIDX
uuid
→ User
group_idFKIDX
uuid
→ Group, nullable
species_idFKIDX
uuid
→ Species
observed_atIDX
timestamptz
DwC: eventDate
geometryIDX
geometry
PostGIS point, GIST index
location_description
text
count
integer
behaviour_notes
text
visibility
enum
private | group | public
verified
boolean
verified_byFK
uuid
→ User, nullable
created_at
timestamptz

Location
DwC: Location
idPK
uuid
name
varchar
slugIDX
varchar
unique
geometryIDX
geometry
polygon or point, GIST index
location_type
enum
park|reserve|marine|urban|rural
country
varchar
region
varchar
state / territory
description
text

Media
DwC: MachineObservation + Audubon Core
idPK
uuid
sighting_idFKIDX
uuid
→ Sighting, nullable (draft)
user_idFKIDX
uuid
→ User
status
enum
draft | attached | processing | ready
blob_url
varchar
Azure Blob Storage
cdn_url
varchar
CDN served URL
media_type
enum
photo | audio | video
file_size
bigint
mime_type
varchar
exif_data
jsonb
full EXIF preserved
observed_at_deviceNEW
timestamptz
from EXIF — never overwritten
exif_latNEW
float
GPS from EXIF
exif_lngNEW
float
GPS from EXIF
gps_stripped
boolean
privacy — GPS removed from CDN copy
synced_atNEW
timestamptz
when server received it
uploaded_at
timestamptz

IngestRecord
preservation layer — never delete
idPK
uuid
source_format
enum
dwc|csv|shapefile|json|pdf|api
source_system
varchar
source_reference
varchar
raw_payload
jsonb
original data, immutable
group_idFK
uuid
→ Group, nullable
submitted_byFK
uuid
→ User
submitted_at
timestamptz
mapped_at
timestamptz
nullable until processed
mapping_confidence
float
0.0 – 1.0
mapping_notes
text
canonical_sighting_idFK
uuid
→ Sighting, nullable

Key relationships
User → Sighting — one user has many sightings
Group → Sighting — one group has many sightings (nullable — sightings can be ungrouped)
User ↔ Group — many-to-many via GroupMembership with role
Species → Sighting — one species has many sightings
Sighting → Media — one sighting has many media (nullable until attached)
Sighting → Location — computed via PostGIS spatial join, not a FK
IngestRecord → Sighting — one ingest record maps to one canonical sighting (nullable until mapped)
User → verified_by on Sighting — curator/admin role only