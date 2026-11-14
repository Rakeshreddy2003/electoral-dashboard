import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { partyTagStyle } from "./partyColors";

interface Candidate {
  position: number;
  candidate_name: string;
  party: string;
  votes: number;
  vote_share_percentage: number;
}

interface YearBlock {
  year: number;
  candidates: Candidate[];
}

export default function TopCandidatesHistory({ acName, pcName, title }: { acName?: string; pcName?: string; title: string }) {
  const [blocks, setBlocks] = useState<YearBlock[]>([]);

  useEffect(() => {
    const params = acName ? { ac_name: acName } : pcName ? { pc_name: pcName } : {};
    if (!acName && !pcName) return;
    api.get("/retrospective/top-candidates", { params }).then((res) => setBlocks(res.data));
  }, [acName, pcName]);

  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <h3>{title}</h3>
      {blocks.length === 0 ? (
        <div className="empty-state">No data</div>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Year</th>
                <th>#</th>
                <th>Candidate</th>
                <th>Party</th>
                <th className="num">Votes</th>
                <th className="num">Vote share %</th>
              </tr>
            </thead>
            <tbody>
              {blocks.map((b) =>
                b.candidates.map((c, i) => (
                  <tr key={`${b.year}-${c.position}`}>
                    {i === 0 ? (
                      <td rowSpan={b.candidates.length} style={{ fontWeight: 700, verticalAlign: "top" }}>
                        {b.year}
                      </td>
                    ) : null}
                    <td>{c.position}</td>
                    <td>{c.candidate_name}</td>
                    <td>
                      <span className="party-tag" style={partyTagStyle(c.party)}>
                        {c.party}
                      </span>
                    </td>
                    <td className="num">{c.votes?.toLocaleString()}</td>
                    <td className="num">{c.vote_share_percentage?.toFixed(1)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
