export default function PageHeader({ title, subtitle }: { title: string; subtitle?: string; accent?: string }) {
  return (
    <div className="page-header">
      <h2>{title}</h2>
      {subtitle && <p>{subtitle}</p>}
    </div>
  );
}
