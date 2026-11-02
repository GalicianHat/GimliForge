const $ = (selector, root=document) => root.querySelector(selector);
const state = {id: null, findings: []};
const severities = ['Crítica','Alta','Media','Baja','Informativa'];

function notice(message, error=false) {
  const box = $('#message'); box.hidden = false; box.textContent = message;
  box.classList.toggle('error', error); box.scrollIntoView({block:'nearest'});
}
async function request(path, options={}) {
  const response = await fetch(path, {cache:'no-store', ...options});
  const contentType = response.headers.get('content-type') || '';
  if (!response.ok) {
    const body = contentType.includes('json') ? await response.json() : {};
    throw new Error(body.error || `Error ${response.status}`);
  }
  return contentType.includes('json') ? response.json() : response.blob();
}
function showEditor() { $('#home').hidden=true; $('#editor').hidden=false; $('#message').hidden=true; window.scrollTo(0,0); }
function showHome() { $('#editor').hidden=true; $('#home').hidden=false; $('#message').hidden=true; refresh(); window.scrollTo(0,0); }
function blankFinding(index) { return {id:`VULN-${String(index).padStart(3,'0')}`,titulo:'',severidad:'Media',cvss:null,categoria:'',activo:'',descripcion_tecnica:'',evidencia:'',impacto:'',reproduccion:'',recomendacion:'',referencias:'',imagenes:[]}; }
function node(tag, attrs={}) { const element=document.createElement(tag); for (const [key,value] of Object.entries(attrs)) { if(key==='text') element.textContent=value; else element.setAttribute(key,value); } return element; }
function field(label, name, value='', type='text', extra={}) {
  const wrapper=node('label',{text:label}); const control=node(type==='textarea'?'textarea':'input', {name,...extra});
  if (extra.class === 'wide') wrapper.classList.add('wide');
  if(type!=='textarea') control.type=type; control.value=value ?? ''; wrapper.append(control); return wrapper;
}
function renderImages(card) {
  const list=$('.evidence-images',card); list.replaceChildren();
  card._images.forEach((image,index)=>{
    const row=node('div',{class:'evidence-item'});
    if(['image/png','image/jpeg'].includes(image.mime)) row.append(node('img',{src:`data:${image.mime};base64,${image.data}`,alt:image.leyenda||image.nombre||`Evidencia ${index+1}`}));
    const label=node('label',{text:'Pie de imagen'});
    const name=node('small',{text:image.nombre||`Imagen ${index+1}`});
    const caption=node('input',{type:'text',maxlength:'300',placeholder:'Qué muestra esta evidencia'});
    caption.value=image.leyenda||'';
    caption.addEventListener('input',()=>{image.leyenda=caption.value;});
    label.append(name,caption); row.append(label);
    const remove=node('button',{type:'button',class:'remove',text:'Quitar'});
    remove.addEventListener('click',()=>{card._images.splice(index,1);renderImages(card);});
    row.append(remove); list.append(row);
  });
}
function readImage(file) {
  return new Promise((resolve,reject)=>{
    const reader=new FileReader();
    reader.onload=()=>resolve(String(reader.result).split(',')[1]);
    reader.onerror=()=>reject(new Error('No se pudo leer la imagen'));
    reader.readAsDataURL(file);
  });
}
function drawFindings() {
  const container=$('#findings'); container.replaceChildren();
  state.findings.forEach((finding,index)=>{
    const card=node('div',{class:'finding'}); card._images=[...(finding.imagenes||[])]; const head=node('div',{class:'finding-head'});
    head.append(node('h4',{text:`Hallazgo ${index+1}`}));
    const remove=node('button',{type:'button',class:'remove',text:'Eliminar'});
    remove.addEventListener('click',()=>{readFindings();state.findings.splice(index,1);drawFindings();});
    head.append(remove); card.append(head);
    const grid=node('div',{class:'finding-fields'});
    grid.append(field('Identificador','id',finding.id,'text',{required:'',maxlength:'80'}));
    grid.append(field('Título','titulo',finding.titulo,'text',{required:'',maxlength:'200'}));
    const severity=node('label',{text:'Severidad'}), select=node('select',{name:'severidad'});
    severities.forEach(value=>{const option=node('option',{value,text:value});select.append(option);}); select.value=finding.severidad;
    severity.append(select); grid.append(severity);
    grid.append(field('CVSS (opcional)','cvss',finding.cvss,'number',{min:'0',max:'10',step:'0.1'}));
    grid.append(field('Categoría','categoria',finding.categoria,'text',{maxlength:'100'}));
    grid.append(field('Activo afectado','activo',finding.activo,'text',{maxlength:'200'}));
    grid.append(field('Descripción técnica','descripcion_tecnica',finding.descripcion_tecnica,'textarea',{required:'',maxlength:'5000',class:'wide'}));
    grid.append(field('Evidencia','evidencia',finding.evidencia,'textarea',{maxlength:'4000',class:'wide'}));
    const evidence=node('div',{class:'evidence-block'});
    evidence.append(node('h5',{text:'Imágenes de evidencia'}),node('p',{text:'Añade hasta 5 capturas PNG o JPEG de 3 MB cada una. Incluye un pie que explique lo que se observa.'}));
    const upload=node('label',{class:'evidence-upload',text:'+ Añadir imágenes'});
    const input=node('input',{type:'file',accept:'image/png,image/jpeg',multiple:''});
    input.addEventListener('change',async()=>{
      try {
        const files=[...input.files];
        if(card._images.length+files.length>5) throw new Error('Máximo 5 imágenes por hallazgo');
        for(const file of files) {
          if(!['image/png','image/jpeg'].includes(file.type)||file.size>3000000) throw new Error('Usa PNG o JPEG de hasta 3 MB por imagen');
          card._images.push({nombre:file.name,mime:file.type,data:await readImage(file),leyenda:''});
        }
        renderImages(card);
      } catch(error) {notice(error.message,true);}
      input.value='';
    });
    upload.append(input); evidence.append(upload,node('div',{class:'evidence-images'})); grid.append(evidence);
    grid.append(field('Impacto','impacto',finding.impacto,'textarea',{maxlength:'3000',class:'wide'}));
    grid.append(field('Reproducción o validación','reproduccion',finding.reproduccion,'textarea',{maxlength:'3000',class:'wide'}));
    grid.append(field('Recomendación','recomendacion',finding.recomendacion,'textarea',{maxlength:'2000',class:'wide'}));
    grid.append(field('Referencias','referencias',finding.referencias,'textarea',{maxlength:'1000',class:'wide'}));
    card.append(grid);container.append(card);renderImages(card);
  });
}
function readFindings() {
  state.findings=[...document.querySelectorAll('.finding')].map(card=>{
    const get=name=>$(`[name="${name}"]`,card).value.trim();
    return {id:get('id'),titulo:get('titulo'),severidad:get('severidad'),cvss:get('cvss')===''?null:Number(get('cvss')),categoria:get('categoria')||'Sin categorizar',activo:get('activo'),descripcion_tecnica:get('descripcion_tecnica'),evidencia:get('evidencia'),impacto:get('impacto'),reproduccion:get('reproduccion'),recomendacion:get('recomendacion'),referencias:get('referencias'),imagenes:card._images||[]};
  });
}
function collect() {
  readFindings(); const form=$('#audit-form');
  const metadata={}; for (const name of ['cliente','auditor','fecha_auditoria','alcance','metodologia','resumen_ejecutivo','impacto_negocio','conclusiones']) metadata[name]=form.elements[name].value.trim();
  return {metadata,hallazgos:state.findings};
}
async function save() {
  if(!$('#audit-form').reportValidity()) return false;
  const path=state.id?`/api/projects/${state.id}`:'/api/projects';
  const result=await request(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(collect())});
  state.id=result.id; $('#editor-title').textContent=$('#audit-form').elements.cliente.value; notice('Auditoría guardada en este equipo.'); return true;
}
function edit(data,id=null) {
  state.id=id; state.findings=data.hallazgos || [];
  const form=$('#audit-form'); form.elements.cliente.value=data.metadata.cliente||''; form.elements.auditor.value=data.metadata.auditor||'';
  form.elements.fecha_auditoria.value=data.metadata.fecha_auditoria||new Date().toISOString().slice(0,10);
  for (const name of ['alcance','metodologia','resumen_ejecutivo','impacto_negocio','conclusiones']) form.elements[name].value=data.metadata[name]||'';
  $('#editor-title').textContent=data.metadata.cliente||'Nueva auditoría'; drawFindings(); showEditor();
}
async function refresh() {
  try { const items=await request('/api/projects'); const list=$('#projects');list.replaceChildren();
    if(!items.length) {list.append(node('div',{class:'empty',text:'Aún no hay auditorías. Crea una o importa un JSON para empezar.'}));return;}
    items.forEach(item=>{const button=node('button',{class:'project',type:'button'});
      button.append(node('small',{text:item.fecha}),node('strong',{text:item.cliente}),node('small',{text:`${item.hallazgos} hallazgos · Abrir proyecto →`}));
      button.addEventListener('click',async()=>{try{edit(await request(`/api/projects/${item.id}`),item.id);}catch(error){notice(error.message,true);}}); list.append(button);});
  } catch(error) {notice(error.message,true);} }
$('#new').addEventListener('click',()=>edit({metadata:{fecha_auditoria:new Date().toISOString().slice(0,10)},hallazgos:[blankFinding(1)]}));
$('#back').addEventListener('click',showHome);
$('#add-finding').addEventListener('click',()=>{readFindings();state.findings.push(blankFinding(state.findings.length+1));drawFindings();});
$('#audit-form').addEventListener('submit',async event=>{event.preventDefault();try{await save();}catch(error){notice(error.message,true);}});
async function refreshGeminiStatus() {
  try {const result=await request('/api/settings/gemini');$('#gemini-status').textContent=result.configured?'Clave configurada en este equipo.':'Aún no hay una clave configurada.';}
  catch(error){$('#gemini-status').textContent=error.message;}
}
$('#gemini-settings-toggle').addEventListener('click',()=>{
  const panel=$('#gemini-settings');panel.hidden=!panel.hidden;
  if(!panel.hidden){refreshGeminiStatus();panel.scrollIntoView({block:'start'});}
});
$('#gemini-key-save').addEventListener('click',async()=>{
  const input=$('#gemini-key');
  try {
    const key=input.value.trim();
    if(!key)throw new Error('Pega primero tu clave API');
    await request('/api/settings/gemini',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key})});
    input.value=''; await refreshGeminiStatus();notice('Clave de Gemini guardada solo en este equipo.');
  }catch(error){notice(error.message,true);}
});
$('#ai-draft').addEventListener('click',async()=>{
  try {
    if(!await save()) return;
    const button=$('#ai-draft'); button.disabled=true; button.textContent='Gemini está redactando…';
    try {
      const proposal=await request(`/api/projects/${state.id}/ai-draft`,{method:'POST'});
      for(const name of ['resumen_ejecutivo','impacto_negocio','conclusiones']) $('#audit-form').elements[name].value=proposal[name];
      for(const item of proposal.hallazgos) {
        const card=[...document.querySelectorAll('.finding')].find(el=>$('[name="id"]',el).value===item.id);
        if(card) for(const name of ['impacto','recomendacion']) $(`[name="${name}"]`,card).value=item[name];
      }
      notice('Propuesta cargada. Revísala y pulsa Guardar auditoría para conservarla.');
    } finally {button.disabled=false;button.textContent='Proponer texto con Gemini';}
  } catch(error) {notice(error.message,true);}
});
$('#import').addEventListener('change',async event=>{const file=event.target.files[0];if(!file)return;
  try{if(file.size>20000000)throw new Error('El archivo supera 20 MB');const data=JSON.parse(await file.text());
    if(!data.metadata && data.cliente) data.metadata={cliente:data.cliente,auditor:data.auditor,fecha_auditoria:data.fecha_auditoria};
    if(Array.isArray(data.hallazgos)) data.hallazgos=data.hallazgos.map(item=>({...blankFinding(0),...item,titulo:item.titulo||item.tipo||'',categoria:item.categoria||'Sin categorizar',cvss:item.cvss??null}));
    edit(data);notice('JSON cargado. Revise los campos y guarde la auditoría.');
  }catch(error){notice(`No se pudo importar: ${error.message}`,true);} event.target.value='';});
for (const format of ['tex','pdf']) $(`#export-${format}`).addEventListener('click',async()=>{
  try{if(!await save())return;const response=await fetch(`/api/projects/${state.id}/export/${format}`);
    if(!response.ok){const body=await response.json();throw new Error(body.error||'No se pudo generar el informe');}
    const isZip=(response.headers.get('content-type')||'').includes('application/zip');
    const filename=isZip?'informe_gimliforge_fuentes.zip':`informe_gimliforge.${format}`;
    const blob=await response.blob(),url=URL.createObjectURL(blob),link=node('a',{href:url,download:filename});
    document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
    notice(isZip?'Fuentes LaTeX e imágenes descargadas en ZIP.':`Informe ${format.toUpperCase()} descargado.`);
  }catch(error){notice(error.message,true);}
});
refresh();
refreshGeminiStatus();
