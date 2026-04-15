/**
 * RelationshipGraph - D3.js force-directed graph of dataset relations.
 * Renders nodes (datasets) and edges (detected relationships).
 */
import { useEffect, useRef } from 'react';

export default function RelationshipGraph({ graph }) {
  const svgRef = useRef(null);

  useEffect(() => {
    if (!graph || !graph.nodes || graph.nodes.length === 0 || !svgRef.current) return;

    // Dynamic import of D3
    import('d3').then(d3 => {
      renderGraph(d3, svgRef.current, graph);
    });
  }, [graph]);

  if (!graph || !graph.nodes || graph.nodes.length === 0) {
    return (
      <div className="empty-state">
        <span className="empty-state-icon">🕸️</span>
        <p className="empty-state-title">Sin relaciones detectadas</p>
        <p style={{ color: 'var(--text-muted)' }}>
          Ejecuta el análisis para visualizar conexiones entre datasets
        </p>
      </div>
    );
  }

  return (
    <div className="graph-container glass-card" style={{ padding: 0 }}>
      <div className="chart-title" style={{ padding: '1rem 1.5rem 0' }}>
        🕸️ Grafo de Relaciones
        <span className="chart-badge badge-correlation">
          {graph.nodes.length} datasets • {graph.edges.length} relaciones
        </span>
      </div>
      <svg ref={svgRef} style={{ width: '100%', height: '500px' }}></svg>
    </div>
  );
}


function renderGraph(d3, svgElement, graph) {
  // Clear previous
  d3.select(svgElement).selectAll('*').remove();

  const width = svgElement.clientWidth || 800;
  const height = 500;

  const svg = d3.select(svgElement)
    .attr('viewBox', `0 0 ${width} ${height}`);

  // Gradient definitions
  const defs = svg.append('defs');
  const gradient = defs.append('linearGradient')
    .attr('id', 'nodeGradient')
    .attr('x1', '0%').attr('y1', '0%')
    .attr('x2', '100%').attr('y2', '100%');
  gradient.append('stop').attr('offset', '0%').attr('stop-color', '#3b82f6');
  gradient.append('stop').attr('offset', '100%').attr('stop-color', '#8b5cf6');

  // Glow filter
  const filter = defs.append('filter').attr('id', 'glow');
  filter.append('feGaussianBlur').attr('stdDeviation', '4').attr('result', 'coloredBlur');
  const feMerge = filter.append('feMerge');
  feMerge.append('feMergeNode').attr('in', 'coloredBlur');
  feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

  // Create simulation
  const simulation = d3.forceSimulation(graph.nodes)
    .force('link', d3.forceLink(graph.edges)
      .id(d => d.id)
      .distance(150)
    )
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(60));

  // Draw edges
  const link = svg.append('g')
    .selectAll('line')
    .data(graph.edges)
    .join('line')
    .attr('stroke', d => {
      const c = d.confidence || 0.5;
      return `rgba(139, 92, 246, ${0.3 + c * 0.5})`;
    })
    .attr('stroke-width', d => 1 + (d.confidence || 0.5) * 2)
    .attr('stroke-dasharray', d => d.confidence < 0.5 ? '5,5' : 'none');

  // Edge labels
  const linkLabel = svg.append('g')
    .selectAll('text')
    .data(graph.edges)
    .join('text')
    .attr('font-size', '9px')
    .attr('fill', '#64748b')
    .attr('text-anchor', 'middle')
    .attr('font-family', 'Inter')
    .text(d => {
      const label = d.label || '';
      return label.length > 30 ? label.substring(0, 30) + '...' : label;
    });

  // Draw nodes
  const node = svg.append('g')
    .selectAll('g')
    .data(graph.nodes)
    .join('g')
    .call(d3.drag()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x; d.fy = d.y;
      })
      .on('drag', (event, d) => {
        d.fx = event.x; d.fy = event.y;
      })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null; d.fy = null;
      })
    );

  // Node circles
  node.append('circle')
    .attr('r', d => 20 + Math.min(Math.log10(d.row_count + 1) * 5, 15))
    .attr('fill', 'url(#nodeGradient)')
    .attr('stroke', 'rgba(255,255,255,0.2)')
    .attr('stroke-width', 2)
    .style('filter', 'url(#glow)')
    .style('cursor', 'pointer');

  // Node labels
  node.append('text')
    .attr('dy', d => 30 + Math.min(Math.log10(d.row_count + 1) * 5, 15))
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('font-weight', '600')
    .attr('fill', '#f1f5f9')
    .attr('font-family', 'Inter')
    .text(d => {
      const name = d.label.replace('.csv', '');
      return name.length > 15 ? name.substring(0, 15) + '…' : name;
    });

  // Row count inside node
  node.append('text')
    .attr('dy', 4)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('font-weight', '700')
    .attr('fill', 'white')
    .attr('font-family', 'Inter')
    .text(d => {
      const n = d.row_count;
      if (n >= 1000000) return (n/1000000).toFixed(1) + 'M';
      if (n >= 1000) return (n/1000).toFixed(1) + 'K';
      return n;
    });

  // Tooltip on hover
  node.append('title')
    .text(d => `${d.label}\n${d.row_count} filas × ${d.column_count} columnas`);

  // Simulation tick
  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y);

    linkLabel
      .attr('x', d => (d.source.x + d.target.x) / 2)
      .attr('y', d => (d.source.y + d.target.y) / 2);

    node.attr('transform', d => `translate(${d.x},${d.y})`);
  });
}
