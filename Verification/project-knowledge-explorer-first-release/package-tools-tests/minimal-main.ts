import './styles.css';
const output = document.querySelector<HTMLDivElement>('#app');
if (output) output.textContent = import.meta.env.EXPLORER_BUILD_ID + ':' + import.meta.env.EXPLORER_SCHEMA_SHA256;
document.querySelector('#load')?.addEventListener('click', async () => { const { default: cytoscape } = await import('cytoscape'); const graph = cytoscape({ headless: true, elements: [{data:{id:'a'}},{data:{id:'b'}},{data:{id:'r', source:'a',target:'b'}}]}); if (output) output.textContent += ':' + graph.edges().length; graph.destroy(); });
