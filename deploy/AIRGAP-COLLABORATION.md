# Offline collaboration gateway deployment checklist

1. Mirror pinned images and OS/package dependencies into an internal registry.
2. Deploy Zulip, Nextcloud and Docmost independently with vendor-supported databases, TLS, backup and restore procedures.
3. Configure PMO_ZULIP_URL, PMO_ZULIP_EMAIL, PMO_ZULIP_API_KEY.
4. Configure PMO_NEXTCLOUD_URL, PMO_NEXTCLOUD_USER, PMO_NEXTCLOUD_APP_PASSWORD.
5. Configure PMO_DOCMOST_URL; Community edition is manual-link-only.
6. Restrict AIPMO egress to approved internal hostnames/IPs. Do not permit arbitrary redirect destinations.
7. Configure PMO_SYNC_WORKER_KEY and PMO_API_KEY as deployment secrets.
8. Run GET /api/v1/collaboration/{provider}/probe using authorized worker credentials.
9. Test internal CA trust, image signatures, SBOM, restore drills and blocked external DNS.
10. Do not assume Docmost Community REST API is available; Enterprise licensing is required.
