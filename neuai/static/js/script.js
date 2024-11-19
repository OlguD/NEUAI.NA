// DOM elementlerini global olarak tanımla
const videoFeed = document.getElementById('videoFeed');
const placeholderImage = document.getElementById('placeholderImage');
const startButton = document.getElementById('startButton');
const stopButton = document.getElementById('stopButton');
const faceAnalyzeButton = document.getElementById('faceAnalyzeButton');
const documentAnalyzeButton = document.getElementById('documentAnalyzeButton');
const detectionMessage = document.getElementById('detectionMessage');
const similarityResults = document.getElementById('similarityResults');

// Durum değişkenleri
let isVideoRunning = false;
let isObjectDetected = false;
let currentObjectType = null;
let detectionInterval = null;

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    startButton.addEventListener('click', startVideo);
    stopButton.addEventListener('click', stopVideo);
    faceAnalyzeButton.addEventListener('click', analyzeFace);
    documentAnalyzeButton.addEventListener('click', analyzeDocument);
});

function startVideo() {
    console.log("Video başlatılıyor...");
    isVideoRunning = true;
    isObjectDetected = false;
    currentObjectType = null;
    
    videoFeed.src = videoFeed.dataset.videoUrl;
    videoFeed.style.display = 'block';
    placeholderImage.style.display = 'none';
    
    startButton.style.display = 'none';
    stopButton.style.display = 'inline-flex';
    
    // Butonları sıfırla
    faceAnalyzeButton.disabled = true;
    documentAnalyzeButton.disabled = true;
    
    // Nesne tespitini başlat
    detectObject();
}

function stopVideo() {
    console.log("Video durduruluyor...");
    isVideoRunning = false;
    isObjectDetected = false;
    currentObjectType = null;
    
    videoFeed.src = "";
    videoFeed.style.display = 'none';
    placeholderImage.style.display = 'flex';
    
    startButton.style.display = 'inline-flex';
    stopButton.style.display = 'none';
    
    // Butonları devre dışı bırak
    faceAnalyzeButton.disabled = true;
    documentAnalyzeButton.disabled = true;
    
    // Sonuçları temizle
    detectionMessage.innerHTML = '';
    similarityResults.innerHTML = '<div class="result-item"><p>Henüz analiz yapılmadı</p></div>';
}

async function detectObject() {
    if (!isVideoRunning) return;

    try {
        const response = await fetch('/detect_object');
        const data = await response.json();
        console.log("Tespit sonucu:", data);

        if (data.error) {
            console.error("Tespit hatası:", data.error);
            if (isVideoRunning) setTimeout(detectObject, 500);
            return;
        }

        if (data.type === 'face') {
            currentObjectType = 'face';
            faceAnalyzeButton.disabled = false;
            documentAnalyzeButton.disabled = true;
            showMessage('Yüz tespit edildi - Yüz analizi yapabilirsiniz');
        }
        else if (data.type === 'document') {
            currentObjectType = 'document';
            documentAnalyzeButton.disabled = false;
            faceAnalyzeButton.disabled = true;
            showMessage('Belge tespit edildi - Belge analizi yapabilirsiniz');
        }
        else {
            if (isVideoRunning) setTimeout(detectObject, 500);
        }
    } catch (error) {
        console.error("Tespit hatası:", error);
        if (isVideoRunning) setTimeout(detectObject, 500);
    }
}

function showMessage(text) {
    if (detectionMessage) {
        detectionMessage.innerHTML = `
            <div class="success-message">
                <i class="fas fa-check-circle"></i>
                ${text}
            </div>
        `;
    }
}

async function analyzeFace() {
    if (!isVideoRunning || currentObjectType !== 'face') return;
    
    try {
        const response = await fetch('/analyze_face');
        const data = await response.json();
        
        if (data.error) {
            similarityResults.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    ${data.error}
                </div>
            `;
            return;
        }
        
        similarityResults.innerHTML = `
            <div class="result-item">
                <p>Benzerlik Skoru: <span class="score">${data.similarity_score.toFixed(1)}%</span></p>
                <p>Cosine Benzerliği: <span class="score">${data.cosine_similarity.toFixed(3)}</span></p>
                <p>Euclidean Mesafesi: <span class="score">${data.euclidean_distance.toFixed(3)}</span></p>
                <p>Sonuç: <span class="score">${data.interpretation}</span></p>
            </div>
        `;
    } catch (error) {
        similarityResults.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                Analiz sırasında bir hata oluştu: ${error.message}
            </div>
        `;
    }
}

async function analyzeDocument() {
    if (!isVideoRunning || currentObjectType !== 'document') return;
    
    try {
        const response = await fetch('/document_analysis');
        const data = await response.json();
        
        if (data.error) {
            similarityResults.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    ${data.error}
                </div>
            `;
            return;
        }
        
        let resultHtml = `
            <div class="result-item">
                <h3>Belge Bilgileri</h3>
        `;
        
        if (data.student_no) resultHtml += `<p>Öğrenci No: <span class="score">${data.student_no}</span></p>`;
        if (data.name_surname) resultHtml += `<p>Ad Soyad: <span class="score">${data.name_surname}</span></p>`;
        if (data.department) resultHtml += `<p>Bölüm: <span class="score">${data.department}</span></p>`;
        if (data.class) resultHtml += `<p>Sınıf: <span class="score">${data.class}</span></p>`;
        
        resultHtml += `</div>`;
        similarityResults.innerHTML = resultHtml;
    } catch (error) {
        similarityResults.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                Belge analizi sırasında bir hata oluştu: ${error.message}
            </div>
        `;
    }
}