function draw(graph, type) {

  var graphSection = d3.select('.graph-section').node().getBoundingClientRect();
  var width = graphSection.width;
  var height = graphSection.height;
  var num_nodes = graph.nodes.length;

  var zoom = d3.zoom().on("zoom", function (event) {
    svg.attr("transform", event.transform);
  });

  var svg = d3.select(".graph-section").append("svg")
    .attr("viewBox", [0, 0, width, height])
    .attr("preserveAspectRatio", "xMidYMid meet")
    .call(zoom)
    .append("g");

  var linkForce = d3.forceLink()
    .id(function (d) { return d.id; })
    .distance(function (d) {
      return num_nodes >= 1000 ? d.ENCODED_DISTANCE : 50*d.ENCODED_DISTANCE; })
    .strength(2);


  var simulation = d3.forceSimulation() 
    .force("link", linkForce)
    .force("charge", d3.forceManyBody())
    .on('tick', ticked);

  if (graph.nodes.length > 1000) {
      simulation.force("grid", gridForce(600, 600));
  } else {
      simulation.force("grid", gridForce(0.5, 0.5));
  }


  const edgeColor = d3.scaleLinear()
    .domain([0, 0.25, 0.5, 0.75, 1].map(d => d * d3.max(graph.links, d => d[type])))
    .range([
      '#2cba00',
      '#a3ff00',
      '#ffd400',
      '#ffa700',
      '#ff0000'
    ])
    .interpolate(d3.interpolateRgb);

  const linkScale = d3.scaleLinear()
    .domain(d3.extent(graph.links, d => d[type]))
    .range([2, 5])
  // create and style links
  var link = svg.append("g")
    .attr("stroke", "#999")
    .attr("stroke-opacity", 0.6)
    .selectAll("line")
    .data(graph.links, d => d.source.id + "-" + d.target.id)
    .join("line")
    .attr("class", "edge")
    .attr("stroke-width", function (d) { return linkScale(d[type]); })
    .attr("stroke", function (d) { return edgeColor(d[type]); });

  const color = d3.scaleLinear()
    .domain([0, 0.25, 0.5, 0.75, 1].map(d => d * d3.max(graph.nodes, d => d[type])))
    .range([
      '#2cba00',
      '#a3ff00',
      '#ffd400',
      '#ffa700',
      '#ff0000'
    ])
    .interpolate(d3.interpolateRgb);

  var nodeScale = d3.scaleLinear()
    .domain([0, d3.max(graph.nodes, function (d) { return d[type]; })])
    .range([3, 10]);


  var node = svg.append("g")
    .selectAll("circle")
    .data(graph.nodes)
    .join("circle")
    .attr("r", function (d) { return (type === null | type === 'flow') ? 3 : nodeScale(d[type]); }) // size nodes based on centrality
    .attr("fill", function (d) { return color(d[type]); })
    .attr("class", "node")
    .call(drag(simulation));

  node.append("title")
    .text(function (d) { return `id: ${d.id}\n${type}: ${d[type]}`; });

  link.append("title")
    .text(function (d) {
      return "source: " + d.source + "\n" + "target: " + d.target + "\n" + `${type}: `+ d[type];
    });

  simulation.nodes(graph.nodes)
    .on("tick", ticked);

  simulation.force("link")
    .links(graph.links);

  svg.append("defs").selectAll("marker")
  .data(graph.links) 
  .enter().append("marker")
  .attr("id", (d, i) => "marker" + i) 
  .attr("viewBox", "0 -5 10 10")
  .attr("refX", 15)
  .attr("refY", -0.5)
  .attr("markerWidth", 3)
  .attr("markerHeight", 3)
  .attr("orient", "auto")
  .append("path")
  .attr("fill", d => edgeColor(d[type])) 
  .attr("d", "M0,-5L10,0L0,5");


  link.attr("marker-end", (d, i) => "url(#marker" + i + ")");

  link.raise();


  function ticked() {

    link
      .attr("x1", function (d) { return d.source.x; })
      .attr("y1", function (d) { return d.source.y; })
      .attr("x2", function (d) { return d.target.x; })
      .attr("y2", function (d) { return d.target.y; });

    node
      .attr("cx", function (d) { return d.x; })
      .attr("cy", function (d) { return d.y; });
  }
  

  function gridForce(gridSizeX, gridSizeY) {
    let nodes;
    function force(alpha) {
      nodes.forEach(node => {
        const gridX = Math.round(node.x / gridSizeX) * gridSizeX;
        const gridY = Math.round(node.y / gridSizeY) * gridSizeY;
        node.vx += (gridX - node.x) * alpha;
        node.vy += (gridY - node.y) * alpha;
      });
    }
    force.initialize = _ => nodes = _;
    return force;
  }


  function drag(simulation) {
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    return d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended);
  }
}