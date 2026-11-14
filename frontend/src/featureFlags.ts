// Temporary flag: hides the Form Responses page entirely -- nav tab removed
// and the route redirects back to Retrospective. The backend's ODK sync is
// also paused independently (see ODK_SYNC_ENABLED in backend/app/config.py);
// this is the frontend-side counterpart so the page itself isn't reachable
// while survey intake is paused. Flip back to true to bring it back.
export const RESPONSES_PAGE_ENABLED = false;
