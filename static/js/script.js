let isVideoRunning = false;
let videoFeed = document.getElementById('videoFeed');
let placeholderImage = document.getElementById('placeholderImage');
let startButton = document.getElementById('startButton');
let stopButton = document.getElementById('stopButton');
let analyzeButton = document.getElementById('analyzeButton');

// Sayfa yüklendiğinde başlangıç durumunu ayarla
document.addEventListener('DOMContentLoaded', function() {
    resetVideoState();
});

function resetVideoState() {
    isVideoRunning = false;
    videoFeed.src = "";
    videoFeed.style.display = 'none';
    placeholderImage.style.display = 'flex';
    startButton.style.display = 'inline-flex';
    stopButton.style.display = 'none';
    analyzeButton.disabled = true;
}

function startVideo() {
    console.log("Video başlatılıyor...");
    isVideoRunning = true;
    
    videoFeed.src = videoFeed.dataset.videoUrl;
    videoFeed.style.display = 'block';
    placeholderImage.style.display = 'none';
    
    startButton.style.display = 'none';
    stopButton.style.display = 'inline-flex';
    analyzeButton.disabled = false;

    videoFeed.onerror = function() {
        console.error("Video yüklenirken hata oluştu");
        resetVideoState();
        alert("Video başlatılırken bir hata oluştu. Lütfen tekrar deneyin.");
    };
}

function stopVideo() {
    console.log("Video durduruluyor...");
    // Video durdurma sırasında hata kontrolünü kaldır
    videoFeed.onerror = null;
    resetVideoState();
}

async function analyzeFace() {
    if (!isVideoRunning) {
        document.getElementById('similarityResults').innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                Lütfen önce videoyu başlatın!
            </div>
        `;
        return;
    }

    analyzeButton.disabled = true;
    document.getElementById('similarityResults').innerHTML = `
        <div class="result-item">
            <p><i class="fas fa-spinner fa-spin"></i> Analiz yapılıyor...</p>
        </div>
    `;

    try {
        const response = await fetch('/analyze_face');
        const data = await response.json();
        console.log("Gelen veri:", data);

        if (!response.ok) {
            throw new Error(data.error || 'Sunucu hatası oluştu');
        }
        
        if (data.error) {
            document.getElementById('similarityResults').innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    ${data.error}
                </div>
            `;
        } else {
            document.getElementById('similarityResults').innerHTML = `
                <div class="result-item">
                    <p>Benzerlik Skoru <span class="score">${data.similarity_score.toFixed(1)}%</span></p>
                    <p>Cosine Benzerliği <span class="score">${data.cosine_similarity.toFixed(3)}</span></p>
                    <p>Euclidean Mesafesi <span class="score">${data.euclidean_distance.toFixed(3)}</span></p>
                    <p>Sonuç <span class="score">${data.interpretation}</span></p>
                </div>
            `;
        }
    } catch (error) {
        console.error("Fetch hatası:", error);
        document.getElementById('similarityResults').innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                Sunucu ile bağlantı hatası oluştu! Hata: ${error.message}
            </div>
        `;
    } finally {
        analyzeButton.disabled = false;
    }
}

window.onbeforeunload = function() {
    if (isVideoRunning) {
        stopVideo();
    }
};