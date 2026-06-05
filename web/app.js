// ============ Global State ============

let currentScript = null;
let currentJob = null;
let autoRefreshInterval = null;

// ============ API Calls ============

const API = {
    async get(endpoint) {
        const res = await fetch('/api' + endpoint);
        if (!res.ok) {
            let detail = '';
            try { const errData = await res.json(); detail = errData.detail; } catch(e) {}
            throw new Error(`API Error: ${res.status} ${detail ? '- ' + detail : ''}`);
        }
        return res.json();
    },

    async post(endpoint, data) {
        const res = await fetch('/api' + endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) {
            let detail = '';
            try { const errData = await res.json(); detail = errData.detail; } catch(e) {}
            throw new Error(`API Error: ${res.status} ${detail ? '- ' + detail : ''}`);
        }
        return res.json();
    },

    async put(endpoint, data) {
        const res = await fetch(`/api${endpoint}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error(`API Error: ${res.status}`);
        return res.json();
    },

    async delete(endpoint) {
        const res = await fetch(`/api${endpoint}`, { method: 'DELETE' });
        if (!res.ok) throw new Error(`API Error: ${res.status}`);
        return res.json();
    }
};

// ============ Navigation ============

document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        switchTab(tab);
        btn.parentElement.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    });
});

function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.getElementById(tabName).classList.add('active');

    const titleMap = {
        'dashboard': 'Dashboard',
        'scripts': 'Mis Guiones',
        'generate': 'Generar Video',
        'videos': 'Mis Videos',
        'jobs': 'Estado de Trabajos'
    };

    document.getElementById('page-title').textContent = titleMap[tabName];

    if (tabName === 'dashboard') loadDashboard();
    if (tabName === 'scripts') loadScripts();
    if (tabName === 'videos') refreshVideosList();
    if (tabName === 'jobs') refreshJobs();
}

// ============ Dashboard ============

async function loadDashboard() {
    try {
        const [scripts, files, jobs] = await Promise.all([
            API.get('/scripts'),
            API.get('/files'),
            API.get('/jobs')
        ]);

        document.getElementById('total-scripts').textContent = scripts.length;
        document.getElementById('total-videos').textContent = files.filter(f => f.name.endsWith('.mp4')).length;
        document.getElementById('total-jobs').textContent = jobs.length;

        const storageSize = (files.reduce((sum, f) => sum + f.size, 0) / 1024 / 1024).toFixed(1);
        document.getElementById('storage-used').textContent = `${storageSize} MB`;

        // Recent jobs
        const recentJobs = jobs.slice(0, 5);
        const jobsHtml = recentJobs.map(job => `
            <div class="job-item">
                <div class="job-info">
                    <div class="job-title">${job.job_id}</div>
                    <div class="job-status">${new Date(job.created_at).toLocaleDateString()}</div>
                </div>
                <span class="job-badge badge-${job.status}">${job.status}</span>
            </div>
        `).join('');

        document.getElementById('recent-jobs').innerHTML = jobsHtml || '<p style="text-align:center;color:var(--text-secondary);">No hay trabajos aún</p>';
    } catch (err) {
        console.error('Error loading dashboard:', err);
    }
}

// ============ Scripts Management ============

async function loadScripts() {
    try {
        const scripts = await API.get('/scripts');
        const html = scripts.map(script => `
            <div class="card">
                <div class="card-header">
                    <div class="card-title">${script.topic}</div>
                    <div class="card-meta">${script.scenes} escenas</div>
                </div>
                <div class="card-footer">
                    <button class="btn-secondary" onclick="editScript('${script.id}')">✏️ Editar</button>
                    <button class="btn-primary" onclick="generateVideoFromScript('${script.id}')">▶️ Generar</button>
                </div>
            </div>
        `).join('');

        document.getElementById('scripts-list').innerHTML = html;

        // Update select
        const select = document.getElementById('script-select');
        select.innerHTML = '<option value="">Cargar un guión...</option>' + scripts.map(s =>
            `<option value="${s.id}">${s.topic} (${s.scenes} escenas)</option>`
        ).join('');
    } catch (err) {
        console.error('Error loading scripts:', err);
    }
}

function openNewScriptModal() {
    currentScript = null;
    document.getElementById('script-modal').classList.add('active');
}

async function editScript(scriptId) {
    try {
        const script = await API.get(`/scripts/${scriptId}`);
        currentScript = { id: scriptId, ...script };

        const html = script.scenes.map((scene, idx) => `
            <div class="scene-editor" style="margin-bottom:20px;padding:15px;background:var(--bg-darker);border-radius:8px;">
                <h4 style="margin-bottom:10px;">Escena ${idx + 1}</h4>
                <input type="text" placeholder="ID" value="${scene.id}" onchange="currentScript.scenes[${idx}].id=this.value" style="width:100%;margin-bottom:10px;padding:8px;background:var(--bg-card);border:1px solid var(--border);border-radius:4px;color:var(--text-primary);">
                <input type="text" placeholder="Título" value="${scene.title}" onchange="currentScript.scenes[${idx}].title=this.value" style="width:100%;margin-bottom:10px;padding:8px;background:var(--bg-card);border:1px solid var(--border);border-radius:4px;color:var(--text-primary);">
                <textarea placeholder="Narración" onchange="currentScript.scenes[${idx}].narration=this.value" style="width:100%;margin-bottom:10px;padding:8px;background:var(--bg-card);border:1px solid var(--border);border-radius:4px;color:var(--text-primary);height:80px;">${scene.narration}</textarea>
            </div>
        `).join('');

        document.getElementById('scenes-editor').innerHTML = html;
        document.getElementById('script-modal').classList.add('active');
    } catch (err) {
        console.error('Error editing script:', err);
    }
}

function closeScriptModal() {
    document.getElementById('script-modal').classList.remove('active');
}

async function saveScript() {
    try {
        if (!currentScript) {
            showStatus('No hay script para guardar', 'error');
            return;
        }

        if (currentScript.id) {
            await API.put(`/scripts/${currentScript.id}`, currentScript);
        } else {
            // New script - save it
            const scriptId = Math.random().toString(36).substr(2, 8);
            // This would need additional implementation
        }

        closeScriptModal();
        loadScripts();
        showStatus('Guión guardado exitosamente', 'success');
    } catch (err) {
        showStatus(`Error: ${err.message}`, 'error');
    }
}

// ============ Video Generation ============

function switchGenerateMode(mode) {
    document.querySelectorAll('.generate-mode').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

    document.getElementById(`${mode}-mode`).classList.add('active');
    event.target.classList.add('active');
}

async function generateWithAI() {
    const topic = document.getElementById('topic-input').value.trim();
    const numScenes = parseInt(document.getElementById('scenes-input').value);

    if (!topic) {
        showStatus('Por favor cuéntame tus ideas', 'error');
        return;
    }

    const statusBox = document.getElementById('ai-status');
    statusBox.style.display = 'block';
    statusBox.textContent = '🔄 Generando guion con Gemini IA...';
    document.getElementById('script-phase').style.display = 'none';

    try {
        const result = await API.post('/scripts/generate', {
            topic: topic,
            num_scenes: numScenes
        });

        statusBox.style.display = 'none';
        document.getElementById('current-script-id').value = result.script_id;

        // Cargar script completo para previsualizarlo
        const script = await API.get(`/scripts/${result.script_id}`);
        const scenesHtml = script.scenes.map(s => `
            <div style="margin-bottom: 15px; border-bottom: 1px solid var(--border-color); padding-bottom: 10px;">
                <strong style="color: var(--primary-color)">${s.title}</strong><br>
                <i style="color: var(--text-secondary)">Narración:</i> ${s.narration}<br>
                <code style="display: block; margin-top: 5px; background: rgba(0,0,0,0.2); padding: 5px; border-radius: 4px;">${s.commands.join('<br>')}</code>
            </div>
        `).join('');

        document.getElementById('script-preview-ai').innerHTML = scenesHtml;
        
        // Rellenar campos de YouTube
        document.getElementById('yt-title').value = script.youtube_title || '';
        document.getElementById('yt-desc').value = script.youtube_description || '';
        document.getElementById('yt-tags').value = JSON.stringify(script.youtube_tags || []);

        document.getElementById('script-phase').style.display = 'block';

        loadScripts();
    } catch (err) {
        statusBox.innerHTML = `❌ Error: ${err.message}`;
    }
}

async function generateVideoPreview() {
    const scriptId = document.getElementById('current-script-id').value;
    if (!scriptId) {
        showStatus('❌ Primero debes generar un guion (Paso 1)', 'error');
        return;
    }

    // Ocultar preview anterior
    document.getElementById('preview-phase').style.display = 'none';
    document.getElementById('btn-generate-preview').disabled = true;
    document.getElementById('btn-generate-preview').textContent = '⏳ Generando...';

    try {
        const result = await API.post(`/videos/generate?script_id=${scriptId}`, {});
        currentJob = result.job_id;
        showProgressModal();
        monitorJobProgress('preview');
    } catch (err) {
        showStatus(`Error: ${err.message}`, 'error');
        document.getElementById('btn-generate-preview').disabled = false;
        document.getElementById('btn-generate-preview').textContent = '🎬 2. Generar Video (y previsualizar)';
    }
}

async function uploadToYoutube() {
    const scriptId = document.getElementById('current-script-id').value;
    if (!scriptId) {
        showStatus('❌ Primero debes generar un guion (Paso 1)', 'error');
        return;
    }

    const ytTitle = document.getElementById('yt-title').value;
    const ytDesc  = document.getElementById('yt-desc').value;
    const ytTags  = JSON.parse(document.getElementById('yt-tags').value || '[]');

    try {
        const result = await API.post(`/videos/generate?script_id=${scriptId}`, {
            upload_to_youtube: true,
            youtube_title: ytTitle,
            youtube_description: ytDesc,
            youtube_tags: ytTags
        });
        currentJob = result.job_id;
        showProgressModal();
        monitorJobProgress('youtube');
    } catch (err) {
        showStatus(`Error: ${err.message}`, 'error');
    }
}

async function generateVideoFromScript(scriptId = null) {
    if (!scriptId) {
        showStatus('Por favor selecciona un guión', 'error');
        return;
    }

    try {
        const result = await API.post(`/videos/generate?script_id=${scriptId}`, {});
        currentJob = result.job_id;
        showProgressModal();
        monitorJobProgress('preview');
    } catch (err) {
        showStatus(`Error: ${err.message}`, 'error');
    }
}

// ============ Job Monitoring ============

function showProgressModal() {
    document.getElementById('progress-modal').classList.add('active');
}

function closeProgressModal() {
    document.getElementById('progress-modal').classList.remove('active');
    if (autoRefreshInterval) clearInterval(autoRefreshInterval);
}

async function monitorJobProgress(action = null) {
    autoRefreshInterval = setInterval(async () => {
        try {
            const job = await API.get(`/jobs/${currentJob}`);

            const progressFill = document.getElementById('progress-fill');
            progressFill.style.width = `${Math.min(job.progress, 100)}%`;
            document.getElementById('progress-text').textContent = job.message;

            const details = document.getElementById('job-details');
            details.innerHTML = `
                <div style="font-size:12px;color:var(--text-secondary);">
                    Job ID: ${job.job_id}<br>
                    Estado: <strong>${job.status}</strong>
                </div>
            `;

            if (job.status === 'completed') {
                document.getElementById('progress-title').textContent = '✅ ¡Video Completado!';
                clearInterval(autoRefreshInterval);

                setTimeout(() => {
                    closeProgressModal();
                    loadDashboard();
                    refreshVideosList();

                    if (action === 'preview' && job.output_files) {
                        // Mostrar el video en el preview inline
                        const videoFile = job.output_files.find(f => f.name === 'video_con_musica.mp4') ||
                                          job.output_files.find(f => f.name.endsWith('.mp4'));
                        if (videoFile) {
                            const videoEl = document.getElementById('video-preview');
                            videoEl.src = videoFile.url + '?t=' + Date.now();
                            document.getElementById('generated-video-url').value = videoFile.url;
                            document.getElementById('preview-phase').style.display = 'block';
                            videoEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            showStatus('✅ Video generado. ¡Revísalo antes de subir!', 'success');
                        }
                        // Restaurar botón
                        const btn = document.getElementById('btn-generate-preview');
                        btn.disabled = false;
                        btn.textContent = '🎬 2. Generar Video (y previsualizar)';

                    } else if (action === 'youtube') {
                        const ytMsg = job.message || '';
                        const urlMatch = ytMsg.match(/https:\/\/youtu\.be\/[\w-]+/);
                        if (urlMatch) {
                            showStatus(`🎉 ¡Subido! <a href="${urlMatch[0]}" target="_blank" style="color:#ff0">${urlMatch[0]}</a>`, 'success');
                        } else {
                            showStatus('✅ Subida a YouTube completada.', 'success');
                        }
                    }
                }, 1500);

            } else if (job.status === 'failed') {
                document.getElementById('progress-title').textContent = '❌ Error en la Generación';
                clearInterval(autoRefreshInterval);
                const btn = document.getElementById('btn-generate-preview');
                if (btn) { btn.disabled = false; btn.textContent = '🎬 2. Generar Video (y previsualizar)'; }
            }
        } catch (err) {
            console.error('Error monitoring job:', err);
        }
    }, 1000);
}

async function refreshJobs() {
    try {
        const jobs = await API.get('/jobs');
        const html = jobs.map(job => `
            <div class="job-item">
                <div class="job-info">
                    <div class="job-title">${job.script_id}</div>
                    <div class="job-status">
                        Job: ${job.job_id.substr(0, 12)}...<br>
                        ${new Date(job.created_at).toLocaleString()}
                    </div>
                </div>
                <div style="text-align:right;">
                    <span class="job-badge badge-${job.status}">${job.status}</span>
                    <div style="font-size:12px;margin-top:5px;color:var(--text-secondary);">
                        ${job.progress}%
                    </div>
                </div>
            </div>
        `).join('');

        document.getElementById('jobs-list').innerHTML = html;
    } catch (err) {
        console.error('Error refreshing jobs:', err);
    }
}

// ============ Videos Management ============

async function refreshVideosList() {
    try {
        const files = await API.get('/files');
        const videos = files.filter(f => f.name.endsWith('.mp4'));

        const html = videos.map(file => `
            <div class="card">
                <div class="card-header">
                    <div class="card-title">🎬 ${file.name}</div>
                    <div class="card-meta">${(file.size / 1024 / 1024).toFixed(1)} MB</div>
                </div>
                <div class="card-footer">
                    <a href="/api/files/${file.name}" download class="btn-primary" style="text-decoration:none;text-align:center;flex:1;">⬇️ Descargar</a>
                    <button class="btn-secondary" onclick="deleteFile('${file.name}')">🗑️ Eliminar</button>
                </div>
            </div>
        `).join('');

        document.getElementById('videos-list').innerHTML = html || '<p style="text-align:center;color:var(--text-secondary);">No hay videos aún</p>';
    } catch (err) {
        console.error('Error loading videos:', err);
    }
}

async function deleteFile(filename) {
    if (!confirm(`¿Eliminar ${filename}?`)) return;

    try {
        await API.delete(`/files/${filename}`);
        showStatus(`${filename} eliminado`, 'success');
        refreshVideosList();
    } catch (err) {
        showStatus(`Error: ${err.message}`, 'error');
    }
}

// ============ Utilities ============

function showStatus(message, type = 'info') {
    const statusBox = document.createElement('div');
    statusBox.className = 'status-box';
    statusBox.style.position = 'fixed';
    statusBox.style.top = '20px';
    statusBox.style.right = '20px';
    statusBox.style.zIndex = '2000';
    statusBox.textContent = message;

    if (type === 'error') statusBox.style.borderColor = 'var(--danger)';
    if (type === 'success') statusBox.style.borderColor = 'var(--success)';

    document.body.appendChild(statusBox);
    setTimeout(() => statusBox.remove(), 3000);
}

// ============ Initialization ============

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();

    // Add event listeners for auto-refresh buttons
    document.querySelectorAll('.btn-icon').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            loadDashboard();
        });
    });
});
