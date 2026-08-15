# Security and privacy

This application is intended to run on `127.0.0.1` for one local user. Do not bind it to a public interface or deploy it to the internet without adding authentication, CSRF protection, upload isolation, and production security review.

Report security issues privately to the repository owner. Do not include real Spotify data, database files, archives, raw JSON, or identifying log content in a report.

The importer rejects unsafe ZIP paths and applies member-count and expanded-size limits. Selected JSON is parsed locally and inserted into SQLite; it is never sent to a third-party service by this project.

