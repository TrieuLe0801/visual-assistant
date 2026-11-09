# ADR 0009 — Bounded generation count and image deletion

Date: 2026-11-09
Status: Accepted
Amends: ADR 0005

## Context

The user requested a choice of up to six generated images and deletion of
images from the library. ADR 0005 previously kept all image parameters out of
the UI. Existing image records can be sources for edits and variations, so
deleting a source must not break saved descendants.

## Decision

- Expose only generation count, from 1 to 6, in the UI. The UI sends one
  `/api/images/generate` request per image, in sequence. Each request creates
  one image. Keep provider, model, size, aspect ratio and all other image
  settings on the server.
- Persist a separate operation and result for every attempt. The UI reloads
  the library after all attempts and reports partial success, so successful
  images remain available after another attempt fails.
- Allow the owner to delete an image that is no longer processing. Delete its
  file and hide its record from all owner-facing image queries. Retain a
  metadata tombstone and parent link in SQLite so saved descendants remain
  valid. Other users receive the same 404 response as for an unknown image.
- Migrate existing SQLite databases by adding the nullable `deleted_at` field
  at initialization. No destructive table rebuild is needed.

## Alternatives considered

- Put all six provider calls behind one HTTP request: rejected because the
  existing Nginx proxy read timeout is 240 seconds, and a sequential group may
  exceed it.
- Hard-delete the image row: rejected because descendants keep foreign-key
  references to their source image.

## Consequences

- Generating six images makes six sequential image-provider calls. It can take
  several minutes and incur six image charges. Separate HTTP requests avoid
  holding the Nginx proxy connection open for the whole set.
- Image file deletion cannot share an atomic transaction with SQLite. The API
  deletes the file before marking the record deleted, so a crash between those
  steps may leave a visible record with a missing file. A failed file deletion
  returns an error and leaves the record visible.
- Deleted image metadata remains in SQLite for lineage but is inaccessible
  through the image API. Backups made before deletion can still contain the
  original file until those backups expire under the operator's policy.

## Review triggers

- Users need cancellation, progress after page reload or higher throughput.
- Deletion must erase metadata or recover from a crash between file and row
  updates automatically.
