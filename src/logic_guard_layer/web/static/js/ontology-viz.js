/**
 * Ontology Visualization using D3.js
 * Terminal-themed force-directed graph for maintenance domain ontology
 */

class OntologyVisualization {
    constructor() {
        this.svg = null;
        this.simulation = null;
        this.data = null;
        this.currentView = 'graph';
        this.currentFilter = 'all';
        this.selectedNode = null;
        this.zoom = null;
        this.g = null;

        // Colors matching terminal theme
        this.colors = {
            component: '#00ff00',      // Terminal green
            event: '#ffaa00',          // Amber
            other: '#00ffff',          // Cyan
            subclass: '#00ff00',       // Green for is-a
            property: '#ff00ff',       // Magenta for properties
            text: '#00ff00',
            textDim: '#008800',
            background: '#001100',
            glow: 'rgba(0, 255, 0, 0.5)'
        };

        this.init();
    }

    async init() {
        this.showLoading(true);

        try {
            await this.loadData();
            this.setupSVG();
            this.setupControls();
            this.renderGraph();

            // Listen for global font size changes
            window.addEventListener('fontsizechange', (e) => {
                this.onFontSizeChange(e.detail.size);
            });
        } catch (error) {
            console.error('Failed to initialize visualization:', error);
            this.showError('Failed to load ontology data');
        } finally {
            this.showLoading(false);
        }
    }

    onFontSizeChange(size) {
        // Calculate relative sizes based on global font size
        const nodeSize = Math.max(10, size - 6);
        const linkSize = Math.max(8, size - 8);

        // Update graph node labels
        if (this.g) {
            this.g.selectAll('.node text')
                .attr('font-size', `${nodeSize}px`);
            this.g.selectAll('.link-label')
                .attr('font-size', `${linkSize}px`);
        }
    }

    async loadData() {
        const response = await fetch('/api/ontology/graph');
        if (!response.ok) {
            throw new Error('Failed to fetch ontology data');
        }
        this.data = await response.json();
        console.log('Loaded ontology data:', this.data);
    }

    setupSVG() {
        const container = document.getElementById('viz-main');
        const width = container.clientWidth - 300; // Account for panel
        const height = container.clientHeight || 500;

        this.svg = d3.select('#ontology-svg')
            .attr('width', width)
            .attr('height', height);

        // Add defs for filters/effects
        const defs = this.svg.append('defs');

        // Glow filter
        const filter = defs.append('filter')
            .attr('id', 'glow')
            .attr('x', '-50%')
            .attr('y', '-50%')
            .attr('width', '200%')
            .attr('height', '200%');

        filter.append('feGaussianBlur')
            .attr('stdDeviation', '3')
            .attr('result', 'coloredBlur');

        const feMerge = filter.append('feMerge');
        feMerge.append('feMergeNode').attr('in', 'coloredBlur');
        feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

        // Arrow marker for edges
        defs.append('marker')
            .attr('id', 'arrow')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 25)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', this.colors.subclass);

        defs.append('marker')
            .attr('id', 'arrow-property')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 25)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', this.colors.property);

        // Setup zoom
        this.zoom = d3.zoom()
            .scaleExtent([0.3, 3])
            .on('zoom', (event) => {
                this.g.attr('transform', event.transform);
            });

        this.svg.call(this.zoom);

        // Main group for transformations
        this.g = this.svg.append('g');
    }

    setupControls() {
        // View mode buttons
        document.querySelectorAll('[data-view]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('[data-view]').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.switchView(e.target.dataset.view);
            });
        });

        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.applyFilter(e.target.dataset.filter);
            });
        });

        // Reset button
        document.getElementById('btn-reset').addEventListener('click', () => {
            this.resetView();
        });

        // Center button
        document.getElementById('btn-center').addEventListener('click', () => {
            this.centerView();
        });
    }

    getFilteredData() {
        if (this.currentFilter === 'all') {
            return {
                nodes: this.data.nodes,
                edges: this.data.edges
            };
        }

        const filteredNodes = this.data.nodes.filter(n => n.category === this.currentFilter);
        const nodeIds = new Set(filteredNodes.map(n => n.id));
        const filteredEdges = this.data.edges.filter(e =>
            nodeIds.has(e.source.id || e.source) && nodeIds.has(e.target.id || e.target)
        );

        return {
            nodes: filteredNodes,
            edges: filteredEdges
        };
    }

    renderGraph() {
        const container = document.getElementById('viz-main');
        const width = container.clientWidth - 300;
        const height = container.clientHeight || 500;

        // Clear previous
        this.g.selectAll('*').remove();

        const { nodes, edges } = this.getFilteredData();

        // Create simulation
        this.simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(edges)
                .id(d => d.id)
                .distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(40));

        // Draw edges
        const link = this.g.append('g')
            .attr('class', 'links')
            .selectAll('line')
            .data(edges)
            .enter()
            .append('line')
            .attr('class', d => `link ${d.type}`)
            .attr('stroke', d => d.type === 'subclass' ? this.colors.subclass : this.colors.property)
            .attr('stroke-width', d => d.type === 'subclass' ? 2 : 1)
            .attr('stroke-dasharray', d => d.type === 'subclass' ? 'none' : '5,5')
            .attr('marker-end', d => d.type === 'subclass' ? 'url(#arrow)' : 'url(#arrow-property)')
            .attr('opacity', 0.6);

        // Edge labels - use CSS variable for font size
        const baseFontSize = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--font-size-base')) || 18;
        const linkFontSize = Math.max(8, baseFontSize - 8);
        const linkLabels = this.g.append('g')
            .attr('class', 'link-labels')
            .selectAll('text')
            .data(edges)
            .enter()
            .append('text')
            .attr('class', 'link-label')
            .attr('fill', this.colors.textDim)
            .attr('font-size', `${linkFontSize}px`)
            .attr('text-anchor', 'middle')
            .text(d => d.label);

        // Draw nodes
        const node = this.g.append('g')
            .attr('class', 'nodes')
            .selectAll('g')
            .data(nodes)
            .enter()
            .append('g')
            .attr('class', 'node')
            .call(d3.drag()
                .on('start', (event, d) => this.dragStarted(event, d))
                .on('drag', (event, d) => this.dragged(event, d))
                .on('end', (event, d) => this.dragEnded(event, d)))
            .on('click', (event, d) => this.selectNode(d));

        // Node circles
        node.append('circle')
            .attr('r', d => d.children && d.children.length > 0 ? 20 : 15)
            .attr('fill', d => this.getNodeColor(d))
            .attr('stroke', d => this.getNodeColor(d))
            .attr('stroke-width', 2)
            .attr('filter', 'url(#glow)')
            .attr('opacity', 0.8);

        // Node labels - use CSS variable for font size
        const nodeFontSize = Math.max(10, baseFontSize - 6);
        node.append('text')
            .attr('dy', 30)
            .attr('text-anchor', 'middle')
            .attr('fill', this.colors.text)
            .attr('font-size', `${nodeFontSize}px`)
            .attr('font-family', 'Share Tech Mono, monospace')
            .text(d => d.id);

        // Update positions
        this.simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            linkLabels
                .attr('x', d => (d.source.x + d.target.x) / 2)
                .attr('y', d => (d.source.y + d.target.y) / 2);

            node.attr('transform', d => `translate(${d.x},${d.y})`);
        });
    }

    getNodeColor(node) {
        switch (node.category) {
            case 'component': return this.colors.component;
            case 'event': return this.colors.event;
            default: return this.colors.other;
        }
    }

    dragStarted(event, d) {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    dragEnded(event, d) {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    selectNode(node) {
        this.selectedNode = node;

        // Highlight selected node
        this.g.selectAll('.node circle')
            .attr('opacity', d => d.id === node.id ? 1 : 0.5)
            .attr('stroke-width', d => d.id === node.id ? 4 : 2);

        // Update details panel
        this.updateDetailsPanel(node);
    }

    updateDetailsPanel(node) {
        const panel = document.getElementById('panel-content');

        // Find related constraints
        const relatedConstraints = this.data.constraints.filter(c =>
            c.expression.toLowerCase().includes(node.id.toLowerCase()) ||
            c.description.toLowerCase().includes(node.id.toLowerCase())
        );

        // Find properties applicable to this node
        const properties = this.data.datatype_properties.filter(p =>
            p.domain.some(d => d === node.original_id || d === node.id)
        );

        // Escape all user-controlled data
        const safeId = this.escapeHtml(node.id);
        const safeType = this.escapeHtml(node.type);
        const safeCategory = this.escapeHtml(node.category);
        const safeParent = this.escapeHtml(node.parent);
        const safeChildren = node.children ? node.children.map(c => this.escapeHtml(c)).join(', ') : '';
        const safeDescription = this.escapeHtml(node.description);

        let html = `
            <div class="detail-section">
                <div class="detail-title">${safeId}</div>
                <div class="detail-row">
                    <span class="detail-label">Type:</span>
                    <span class="detail-value">${safeType}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Category:</span>
                    <span class="detail-value category-${safeCategory}">${safeCategory}</span>
                </div>
                ${node.parent ? `
                <div class="detail-row">
                    <span class="detail-label">Parent:</span>
                    <span class="detail-value">${safeParent}</span>
                </div>
                ` : ''}
                ${node.children && node.children.length > 0 ? `
                <div class="detail-row">
                    <span class="detail-label">Children:</span>
                    <span class="detail-value">${safeChildren}</span>
                </div>
                ` : ''}
                ${node.description ? `
                <div class="detail-row">
                    <span class="detail-label">Description:</span>
                    <span class="detail-value">${safeDescription}</span>
                </div>
                ` : ''}
            </div>
        `;

        if (properties.length > 0) {
            html += `
                <div class="detail-section">
                    <div class="detail-subtitle">Properties</div>
                    ${properties.map(p => `
                        <div class="detail-row">
                            <span class="detail-label">${this.escapeHtml(p.id)}:</span>
                            <span class="detail-value">${this.escapeHtml(p.range)}</span>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        if (relatedConstraints.length > 0) {
            html += `
                <div class="detail-section">
                    <div class="detail-subtitle">Related Constraints</div>
                    ${relatedConstraints.map(c => `
                        <div class="constraint-item">
                            <div class="constraint-id">[${this.escapeHtml(c.id)}] ${this.escapeHtml(c.name)}</div>
                            <div class="constraint-expr">${this.escapeHtml(c.expression)}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        panel.innerHTML = html;
    }

    switchView(view) {
        this.currentView = view;

        const svg = document.getElementById('ontology-svg');
        const treeView = document.getElementById('tree-view');
        const constraintsView = document.getElementById('constraints-view');

        // Hide all
        svg.classList.add('hidden');
        treeView.classList.add('hidden');
        constraintsView.classList.add('hidden');

        switch (view) {
            case 'graph':
                svg.classList.remove('hidden');
                break;
            case 'tree':
                treeView.classList.remove('hidden');
                this.renderTree();
                break;
            case 'constraints':
                constraintsView.classList.remove('hidden');
                this.renderConstraints();
                break;
        }
    }

    renderTree() {
        const container = document.getElementById('tree-view');

        // Build tree structure
        const buildTree = (nodes, parentId = null) => {
            return nodes
                .filter(n => n.parent === parentId)
                .map(n => ({
                    ...n,
                    children: buildTree(nodes, n.id)
                }));
        };

        const { nodes } = this.getFilteredData();
        const roots = nodes.filter(n => !n.parent);

        const renderNode = (node, depth = 0) => {
            const indent = '    '.repeat(depth);
            const prefix = depth === 0 ? '' : (node === roots[roots.length - 1] ? '\\-- ' : '+-- ');
            const children = nodes.filter(n => n.parent === node.id);

            // Use escapeHtml for user-controlled data
            const safeCategory = this.escapeHtml(node.category);
            const safeId = this.escapeHtml(node.id);

            let html = `<div class="tree-node category-${safeCategory}">`;
            html += `<span class="tree-indent">${indent}${prefix}</span>`;
            html += `<span class="tree-label" data-node-id="${safeId}">${safeId}</span>`;
            html += `</div>`;

            children.forEach((child, i) => {
                html += renderNode(child, depth + 1);
            });

            return html;
        };

        let html = '<div class="tree-container">';
        roots.forEach(root => {
            html += renderNode(root);
        });
        html += '</div>';

        container.innerHTML = html;

        // Add click handlers
        container.querySelectorAll('.tree-label').forEach(label => {
            label.addEventListener('click', () => {
                const nodeId = label.dataset.nodeId;
                const node = this.data.nodes.find(n => n.id === nodeId);
                if (node) this.updateDetailsPanel(node);
            });
        });
    }

    renderConstraints() {
        const container = document.getElementById('constraints-view');

        const constraintsByType = {};
        this.data.constraints.forEach(c => {
            if (!constraintsByType[c.type]) {
                constraintsByType[c.type] = [];
            }
            constraintsByType[c.type].push(c);
        });

        let html = '<div class="constraints-container">';

        for (const [type, constraints] of Object.entries(constraintsByType)) {
            const safeType = this.escapeHtml(type.toUpperCase());
            html += `
                <div class="constraint-group">
                    <div class="constraint-type">${safeType} CONSTRAINTS</div>
                    ${constraints.map(c => `
                        <div class="constraint-card">
                            <div class="constraint-header">
                                <span class="constraint-id">[${this.escapeHtml(c.id)}]</span>
                                <span class="constraint-name">${this.escapeHtml(c.name)}</span>
                            </div>
                            <div class="constraint-body">
                                <div class="constraint-expr">${this.escapeHtml(c.expression)}</div>
                                <div class="constraint-desc">${this.escapeHtml(c.description)}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        html += '</div>';
        container.innerHTML = html;
    }

    applyFilter(filter) {
        this.currentFilter = filter;
        if (this.currentView === 'graph') {
            this.renderGraph();
        } else if (this.currentView === 'tree') {
            this.renderTree();
        }
    }

    resetView() {
        this.svg.transition()
            .duration(750)
            .call(this.zoom.transform, d3.zoomIdentity);

        // Deselect node
        this.selectedNode = null;
        this.g.selectAll('.node circle')
            .attr('opacity', 0.8)
            .attr('stroke-width', 2);

        document.getElementById('panel-content').innerHTML = '<p class="hint-text">Click on a node to view details</p>';
    }

    centerView() {
        const container = document.getElementById('viz-main');
        const width = container.clientWidth - 300;
        const height = container.clientHeight || 500;

        this.svg.transition()
            .duration(750)
            .call(this.zoom.transform, d3.zoomIdentity.translate(width / 2, height / 2).scale(1));
    }

    showLoading(show) {
        const loading = document.getElementById('loading');
        if (show) {
            loading.classList.add('visible');
        } else {
            loading.classList.remove('visible');
        }
    }

    showError(message) {
        const panel = document.getElementById('panel-content');
        panel.innerHTML = '';
        const errorP = document.createElement('p');
        errorP.className = 'error-text';
        errorP.textContent = 'ERROR: ' + message;
        panel.appendChild(errorP);
    }

    /**
     * Helper to safely escape HTML
     */
    escapeHtml(str) {
        if (str === null || str === undefined) return '';
        const div = document.createElement('div');
        div.textContent = String(str);
        return div.innerHTML;
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.ontologyViz = new OntologyVisualization();
});
