(() => {
  const namespace = "http://www.w3.org/2000/svg";
  function element(tag, attributes = {}, text) {
    const node = document.createElementNS(namespace, tag);
    Object.entries(attributes).forEach(([name, value]) => node.setAttribute(name, value));
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function label(svg, x, y, text, attributes = {}) {
    svg.append(element("text", {x, y, ...attributes}, text));
  }
  function layerRectangle(svg, layer, x, y, width, height) {
    const group = element("g");
    group.append(element("rect", {x, y, width, height, fill: layer.color, stroke: "#444", "stroke-width": 0.5}));
    group.layerInformation = layer;
    svg.append(group);
    return group;
  }
  function installInteractions(svg) {
    const container = svg.parentElement;
    const tooltip = container.querySelector(".stack-tooltip");
    const width = Number(svg.getAttribute("width"));
    const height = Number(svg.getAttribute("height"));
    let view = {x: 0, y: 0, width, height};
    let dragging = null;
    const update = () => svg.setAttribute("viewBox", `${view.x} ${view.y} ${view.width} ${view.height}`);
    const reset = () => { view = {x: 0, y: 0, width, height}; update(); };
    reset();
    svg.addEventListener("mousemove", event => {
      const layer = event.target.closest("g")?.layerInformation;
      if (!layer || dragging) { tooltip.hidden = true; return; }
      const lines = [layer.name, `GDS: ${layer.gds ?? "N/A"}`, `Material: ${layer.material}`];
      if (layer.type) lines.push(`Type: ${layer.type}`);
      if (layer.width !== undefined) lines.push(`Width: ${layer.width} µm`, `Offset: ${layer.offset} µm`);
      lines.push(`z: ${layer.zmin}–${layer.zmax} µm`, `Thickness: ${layer.thickness} µm`);
      tooltip.textContent = lines.join("\n");
      tooltip.hidden = false;
      const bounds = container.getBoundingClientRect();
      tooltip.style.left = `${event.clientX - bounds.left + container.scrollLeft + 12}px`;
      tooltip.style.top = `${event.clientY - bounds.top + container.scrollTop + 12}px`;
    });
    svg.addEventListener("mouseleave", () => { tooltip.hidden = true; });
    svg.addEventListener("wheel", event => {
      if (!event.ctrlKey) return;
      event.preventDefault();
      tooltip.hidden = true;
      const factor = event.deltaY > 0 ? 1.12 : 1 / 1.12;
      const bounds = svg.getBoundingClientRect();
      const xFraction = (event.clientX - bounds.left) / bounds.width;
      const yFraction = (event.clientY - bounds.top) / bounds.height;
      view.x += xFraction * view.width * (1 - factor);
      view.y += yFraction * view.height * (1 - factor);
      view.width *= factor;
      view.height *= factor;
      update();
    }, {passive: false});
    svg.addEventListener("pointerdown", event => {
      if (event.button !== 0) return;
      const bounds = svg.getBoundingClientRect();
      dragging = {x: event.clientX, y: event.clientY, viewX: view.x, viewY: view.y,
        xScale: view.width / bounds.width, yScale: view.height / bounds.height};
      svg.setPointerCapture(event.pointerId);
      svg.style.cursor = "grabbing";
    });
    svg.addEventListener("pointermove", event => {
      if (!dragging) return;
      view.x = dragging.viewX - (event.clientX - dragging.x) * dragging.xScale;
      view.y = dragging.viewY - (event.clientY - dragging.y) * dragging.yScale;
      update();
    });
    const finishDrag = () => { dragging = null; svg.style.cursor = ""; };
    svg.addEventListener("pointerup", finishDrag);
    svg.addEventListener("pointercancel", finishDrag);
    svg.addEventListener("dblclick", reset);
    return reset;
  }
  function renderStack(svg, data, mode) {
    svg.replaceChildren();
    label(svg, 300, 25, "Layer Stack", {"text-anchor": "middle", "font-size": 16});
    if (mode === "scale") {
      data.ticks.forEach(tick => {
        svg.append(element("line", {x1: 75, y1: tick.py, x2: 510, y2: tick.py, stroke: "#ddd"}));
        label(svg, 68, tick.py + 4, `${tick.z} µm`, {"text-anchor": "end"});
      });
    }
    data.layers.forEach(layer => {
      const scaled = mode === "scale";
      const width = 420 / (scaled ? layer.ncols : 1);
      const x = 80 + (scaled ? layer.col * width : 0);
      const y = scaled ? layer.sy : layer.uy;
      const height = scaled ? layer.sh : layer.uh;
      const group = layerRectangle(svg, layer, x, y, width, height);
      if (!scaled || (height >= 14 && width > layer.name.length * 6)) {
        const text = element("text", {x: x + width / 2, y: y + height / 2 + 4,
          "text-anchor": "middle", fill: "#111", stroke: layer.color,
          "stroke-width": 3, "paint-order": "stroke"}, layer.name);
        group.append(text);
      }
      if (!scaled) label(svg, 510, y + height / 2 + 4, layer.gds ?? "N/A", {fill: "#666"});
    });
  }
  function renderCrossSections(svg, data) {
    const crossSections = data.cross_sections;
    label(svg, 500, 25, "PDK Cross-Sections", {"text-anchor": "middle", "font-size": 16});
    if (!crossSections.length) { label(svg, 60, 70, "No registered cross-sections match the layer stack."); return; }
    const bottom = Math.min(...data.layers.map(layer => layer.zmin));
    const top = Math.max(...data.layers.map(layer => layer.zmax));
    const yPosition = z => 45 + 340 * (top - z) / (top - bottom || 1);
    data.ticks.forEach(tick => {
      const y = yPosition(tick.z);
      svg.append(element("line", {x1: 75, y1: y, x2: 980, y2: y, stroke: "#ddd"}));
      label(svg, 68, y + 4, `${tick.z} µm`, {"text-anchor": "end"});
    });
    const columnWidth = 900 / crossSections.length;
    crossSections.forEach((crossSection, index) => {
      const halfExtent = Math.max(...crossSection.layers.map(layer =>
        Math.abs(layer.offset) + layer.width / 2)) * 1.2 || 1;
      const xScale = (columnWidth - 20) / (2 * halfExtent);
      const center = 80 + (index + 0.5) * columnWidth;
      crossSection.layers.forEach(layer => {
        const y = yPosition(layer.zmax);
        layerRectangle(svg, layer, center + (layer.offset - layer.width / 2) * xScale,
          y, layer.width * xScale, Math.max(yPosition(layer.zmin) - y, 1));
      });
      const caption = crossSection.layers.length === 1
        ? `${crossSection.name} (${crossSection.layers[0].width} µm)` : crossSection.name;
      label(svg, center, 410, caption, {"text-anchor": "end",
        transform: `rotate(-35 ${center} 410)`});
    });
  }
  document.querySelectorAll(".layer-stack-viz").forEach(root => {
    const data = JSON.parse(root.querySelector(".stack-data").textContent);
    const stack = root.querySelector(".stack-svg");
    const crossSections = root.querySelector(".cross-section-svg");
    renderStack(stack, data, "uniform");
    const resetStack = installInteractions(stack);
    renderCrossSections(crossSections, data);
    installInteractions(crossSections);
    root.querySelectorAll("button[data-mode]").forEach(button => {
      button.addEventListener("click", () => {
        root.querySelectorAll("button[data-mode]").forEach(other =>
          other.setAttribute("aria-pressed", String(other === button)));
        renderStack(stack, data, button.dataset.mode);
        resetStack();
      });
    });
  });
})();
