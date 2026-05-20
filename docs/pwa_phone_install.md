# PWA Phone Install Guide

This project now has the basic PWA files:

- `frontend/public/manifest.webmanifest`
- `frontend/public/sw.js`
- `frontend/public/icons/icon.svg`
- `frontend/public/icons/icon-192.png`
- `frontend/public/icons/icon-512.png`

## Important Limitation

A real installable PWA normally requires HTTPS.

`http://localhost` is allowed on the same device, but your phone is opening the app through a LAN address such as:

```text
http://192.168.1.107:5173
```

That address is not HTTPS, so Chrome on the phone may only show "Add to Home screen" as a shortcut instead of a full PWA install.

## Current Free Testing Path

Use the LAN browser version for family testing first:

```text
http://192.168.1.107:5173
```

This is enough to test the product experience.

## Full PWA Install Path

To test full PWA installation later, use one of these free or low-cost paths:

1. Deploy the frontend to an HTTPS host such as Vercel, Netlify, or GitHub Pages.
2. Keep the backend on your computer for local testing, or later move it to a small backend host.
3. Open the HTTPS frontend on Android Chrome.
4. Tap the browser menu.
5. Choose "Install app" or "Add to Home screen".

## Notes

The installed PWA can cache the frontend shell, but AI planning still needs the backend and model API to be reachable.
