// `accent`, when it names a word that actually occurs in `title`, renders
// just that word in the app's one signature display moment (Playfair
// Display italic) -- echoing crawindia.com's own "the *signals* of
// democracy" treatment. Everything else in the title stays the plain
// display face; this is deliberately used once per page, not everywhere.
export default function PageHeader({ title, subtitle, accent }: { title: string; subtitle?: string; accent?: string }) {
  const parts = accent && title.includes(accent) ? title.split(accent) : null;
  return (
    <div className="page-header">
      <h2>
        {parts ? (
          <>
            {parts[0]}
            <em>{accent}</em>
            {parts.slice(1).join(accent)}
          </>
        ) : (
          title
        )}
      </h2>
      {subtitle && <p>{subtitle}</p>}
    </div>
  );
}
