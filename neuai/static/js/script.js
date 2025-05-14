const videoFeed = document.getElementById('videoFeed');
const placeholderImage = document.getElementById('placeholderImage');
const startButton = document.getElementById('startButton');
const stopButton = document.getElementById('stopButton');
const faceAnalyzeButton = document.getElementById('faceAnalyzeButton');
const documentAnalyzeButton = document.getElementById('documentAnalyzeButton');
const detectionMessage = document.getElementById('detectionMessage');
const similarityResults = document.getElementById('similarityResults');
const loadingAnimation = document.getElementById('loadingAnimation');
const resetButton = document.getElementById('resetButton');
const confirmButton = document.getElementById('confirmButton');
const rejectButton = document.getElementById('rejectButton');
const controlsSecondary = document.querySelector('.controls-secondary');
const searchIcon = document.getElementsByClassName('search-icon')[0];
const schoolNumberInput = document.getElementById('schoolNumber');

let schoolNumber;
let documentAnalysisResults = null;
let studentImageHtml = null; // Öğrenci fotoğrafını saklamak için yeni değişken
let studentData = null; // Keep track of student data for saving
let faceAnalysisResults = null; // Store face analysis results
let selectedCourses = []; // Store selected courses

// Durum değişkenleri
let isVideoRunning = false;
let isObjectDetected = false;
let currentObjectType = null;
let detectionInterval = null;
let isFaceAnalyzed = false; // Track if face has been analyzed

// Add translation objects near the top of the file
const translations = {
    en: {
        studentNumber: "Student Number",
        studentInformation: "Student Information",
        documentInformation: "Document Information",
        nameSurname: "Name Surname",
        department: "Department",
        class: "Class",
        faceAnalysisResults: "Face Analysis Results",
        similarityScore: "Similarity Score",
        result: "Result",
        searching: "Searching for student...",
        studentNotFound: "Student not found",
        searchError: "An error occurred during the search",
        noAnalysis: "No analysis has been done yet",
        faceAnalysisInProgress: "Face analysis in progress...",
        documentAnalysisInProgress: "Document analysis in progress...",
        
        // New message translations
        faceDetected: "Face detected - You can analyze the face",
        documentDetected: "Document detected - You can analyze the document",
        mostLikelySamePerson: "Most likely the same person",
        resetAnalysis: "Analysis results have been reset. You can start a new analysis.",
        enterSchoolNumber: "Please enter a school number first",
        exactlyEightDigits: "School number must be exactly 8 digits",
        noStudentSelected: "Error: No student selected",
        selectCourse: "Please select at least one course",
        attendanceSaved: "Attendance successfully saved!",
        attendanceRejected: "Attendance rejected. Ready for next student.",
        savingAttendance: "Saving attendance data...",
        excelDownloaded: "Excel file successfully downloaded!",
        generatingExcel: "Generating Excel export...",
        exportFailed: "Export failed",
        similarFeatures: "Similar features present",
        differentPersons: "Different persons"
    },
    tr: {
        studentNumber: "Öğrenci Numarası",
        studentInformation: "Öğrenci Bilgileri",
        documentInformation: "Belge Bilgileri",
        nameSurname: "Ad Soyad",
        department: "Bölüm",
        class: "Sınıf",
        faceAnalysisResults: "Yüz Analiz Sonuçları",
        similarityScore: "Benzerlik Puanı",
        result: "Sonuç",
        searching: "Öğrenci aranıyor...",
        studentNotFound: "Öğrenci bulunamadı",
        searchError: "Arama sırasında bir hata oluştu",
        noAnalysis: "Henüz analiz yapılmadı",
        faceAnalysisInProgress: "Yüz analizi yapılıyor...",
        documentAnalysisInProgress: "Belge analizi yapılıyor...",
        
        // New message translations
        faceDetected: "Yüz tespit edildi - Yüzü analiz edebilirsiniz",
        documentDetected: "Belge tespit edildi - Belgeyi analiz edebilirsiniz",
        mostLikelySamePerson: "Büyük olasılıkla aynı kişi",
        resetAnalysis: "Analiz sonuçları sıfırlandı. Yeni bir analiz başlatabilirsiniz.",
        enterSchoolNumber: "Lütfen önce bir okul numarası girin",
        exactlyEightDigits: "Okul numarası tam olarak 8 rakam olmalıdır",
        noStudentSelected: "Hata: Öğrenci seçilmedi",
        selectCourse: "Lütfen en az bir ders seçin",
        attendanceSaved: "Katılım başarıyla kaydedildi!",
        attendanceRejected: "Katılım reddedildi. Sonraki öğrenci için hazır.",
        savingAttendance: "Katılım verileri kaydediliyor...",
        excelDownloaded: "Excel dosyası başarıyla indirildi!",
        generatingExcel: "Excel dışa aktarımı oluşturuluyor...",
        exportFailed: "Dışa aktarma başarısız oldu",
        similarFeatures: "Benzer özellikler mevcut",
        differentPersons: "Farklı kişiler"
    }
};

// Helper function to get translation based on current language
function getTranslation(key) {
    const lang = localStorage.getItem('preferredLanguage') || 'en';
    return translations[lang][key] || key;
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    startButton.addEventListener('click', startVideo);
    stopButton.addEventListener('click', stopVideo);
    faceAnalyzeButton.addEventListener('click', analyzeFace);
    documentAnalyzeButton.addEventListener('click', analyzeDocument);
    resetButton.addEventListener('click', resetAnalysis);
    confirmButton.addEventListener('click', confirmAttendance);
    rejectButton.addEventListener('click', rejectAttendance);
    
    // Update the school number input event handlers
    schoolNumberInput.addEventListener('keypress', async function(e) {
        if(e.key === 'Enter') {
            e.preventDefault();
            handleSearch();
        }
    });

    // Remove the search icon event listener since we no longer have this element
    // searchIcon.addEventListener('click', function() {
    //     handleSearch();
    // });

    resetButton.disabled = true;

    // Add input validation for numbers only
    schoolNumberInput.addEventListener('input', function(e) {
        // Replace any non-digit character with empty string
        this.value = this.value.replace(/\D/g, '');
    });
});

// Add new function to handle search
async function handleSearch() {
    const inputValue = schoolNumberInput.value.trim();
    if (!inputValue) return;

    // Check if input is exactly 8 digits
    if (!/^\d{8}$/.test(inputValue)) {
        similarityResults.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                ${getTranslation('exactlyEightDigits')}
            </div>
        `;
        return;
    }

    schoolNumber = inputValue;
    await searchStudentByNumber(inputValue);
}

function showLoadingAnimation() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.style.display = 'flex';
    }
}

function hideLoadingAnimation() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.style.display = 'none';
    }
}

function resetAnalysis() {
    // Reset variables
    schoolNumber = null;
    documentAnalysisResults = null;
    studentImageHtml = null;
    
    // Reset similarity results
    similarityResults.innerHTML = `<div class="result-item"><p>${getTranslation('noAnalysis')}</p></div>`;
    
    // Reset school number input
    if (schoolNumberInput) {
        schoolNumberInput.value = '';
    }

    // Reset file input and preview
    const fileInput = document.getElementById('documentFile');
    const previewContainer = document.getElementById('imagePreviewContainer');
    if (fileInput) {
        fileInput.value = ''; // Clear file input
    }
    if (previewContainer) {
        previewContainer.style.display = 'none'; // Hide preview
    }

    // Reset analyze buttons
    faceAnalyzeButton.classList.remove('active');
    documentAnalyzeButton.classList.remove('active');
    
    resetButton.disabled = true;
    
    showMessage(getTranslation('resetAnalysis'));
    
    setTimeout(() => {
        if (isVideoRunning) {
            detectObject();
        }
    }, 1500);
}

function startVideo() {
    console.log("Starting Stream...");
    isVideoRunning = true;
    isObjectDetected = false;
    currentObjectType = null;
    
    videoFeed.src = videoFeed.dataset.videoUrl;
    videoFeed.style.display = 'block';
    placeholderImage.style.display = 'none';
    
    startButton.style.display = 'none';
    stopButton.style.display = 'inline-flex';

    controlsSecondary.style.display = 'flex';
    
    // Butonları sıfırla
    faceAnalyzeButton.disabled = true;
    documentAnalyzeButton.disabled = true;
    resetButton.disabled = true;  // Keep reset disabled until detection
    
    // Nesne tespitini başlat
    detectObject();
}

function stopVideo() {
    console.log("Stoping Stream...");
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

    controlsSecondary.style.display = 'none';
}

function detectObject() {
    if (!isVideoRunning) return;

    fetch('/detect_object')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error("Detection Error:", data.error);
                if (isVideoRunning) setTimeout(detectObject, 500);
                return;
            }

            if (data.type === 'face' || data.type === 'document') {
                resetButton.disabled = false;  // Enable reset button on first detection
                if (data.type === 'face') {
                    currentObjectType = 'face';
                    faceAnalyzeButton.disabled = false;
                    documentAnalyzeButton.disabled = true;
                    faceAnalyzeButton.classList.add('active');
                    documentAnalyzeButton.classList.remove('active');
                    showMessage(getTranslation('faceDetected'));
                }
                else if (data.type === 'document') {
                    currentObjectType = 'document';
                    documentAnalyzeButton.disabled = false;
                    faceAnalyzeButton.disabled = true;
                    documentAnalyzeButton.classList.add('active');
                    faceAnalyzeButton.classList.remove('active');
                    showMessage(getTranslation('documentDetected'));
                }
            }
            else {
                faceAnalyzeButton.classList.remove('active');
                documentAnalyzeButton.classList.remove('active');
                if (isVideoRunning) setTimeout(detectObject, 500);
            }
        })
        .catch(error => {
            console.error("Detection Error:", error);
            if (isVideoRunning) setTimeout(detectObject, 500);
        });
}

function showMessage(text) {
    if (detectionMessage) {
        detectionMessage.innerHTML = `
            <div class="success-message">
                <i class="fas fa-check-circle"></i>
                ${text}
            </div>
        `;
        
        // Auto-hide reset analysis message after 3 seconds
        if (text === getTranslation('resetAnalysis')) {
            setTimeout(() => {
                detectionMessage.innerHTML = '';
            }, 3000);
        }
    }
}

async function analyzeFace() {
    if (!isVideoRunning || currentObjectType !== 'face') return;
    
    if (!schoolNumber) {
        similarityResults.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                ${getTranslation('enterSchoolNumber')}
            </div>
        `;
        return;
    }

    // Loading göster
    similarityResults.innerHTML = `
        <div class="loading-container">
            <div class="loader"></div>
            <span>${getTranslation('faceAnalysisInProgress')}</span>
        </div>
    `;
    
    try {
        const response = await fetch('/analyze_face', {
            headers: {
                'X-School-Number': schoolNumber
            }
        });
        const data = await response.json();
        
        // Store face analysis results
        faceAnalysisResults = data;
        // Mark face as analyzed
        isFaceAnalyzed = true;
        
        let resultHtml = '';
        
        // Sadece öğrencinin okul numarasını göster
        if (!documentAnalysisResults) {
            resultHtml += `
                <div class="document-analysis-results">
                    <div class="result-item">
                        <h3>${getTranslation('studentInformation')}</h3>
                        <p>${getTranslation('studentNumber')}: <span class="score">${schoolNumber}</span></p>
                    </div>
                </div>
            `;
        }

        // Öğrenci fotoğrafını göster
        resultHtml += `
            <div class="result-item">
                <div class="student-image">
                    <img src="/get_student_image/${schoolNumber}" alt="Student Image" 
                         style="width: 100px; height: 120px; object-fit: cover;">
                </div>
            </div>
        `;
        
        // Yüz analizi sonuçlarını ekle
        if (data.error) {
            resultHtml += `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    ${data.error}
                </div>
            `;
        } else {
            // Check if data.interpretation matches the English text and replace with translation if needed
            let interpretation = data.interpretation;
            if (interpretation === "Most likely the same person") {
                interpretation = getTranslation('mostLikelySamePerson');
            } else if (interpretation === "Similar features present") {
                interpretation = getTranslation('similarFeatures');
            } else if (interpretation === "Different persons") {
                interpretation = getTranslation('differentPersons');
            }
            
            resultHtml += `
                <div class="result-item">
                    <h3>${getTranslation('faceAnalysisResults')}</h3>
                    <p>${getTranslation('similarityScore')}: <span class="score">${data.similarity_score.toFixed(1)}%</span></p>
                    <p>${getTranslation('result')}: <span class="score">${interpretation}</span></p>
                </div>
            `;
        }
        
        // Belge analizi sonuçları varsa ekle
        if (documentAnalysisResults) {
            resultHtml += `
                <div class="result-item">
                    <h3>${getTranslation('documentInformation')}</h3>
                    ${documentAnalysisResults.name_surname ? `<p>${getTranslation('nameSurname')}: <span class="score">${documentAnalysisResults.name_surname}</span></p>` : ''}
                    ${documentAnalysisResults.department ? `<p>${getTranslation('department')}: <span class="score">${documentAnalysisResults.department}</span></p>` : ''}
                    ${documentAnalysisResults.class ? `<p>${getTranslation('class')}: <span class="score">${documentAnalysisResults.class}</span></p>` : ''}
                </div>
            `;
        }

        similarityResults.innerHTML = resultHtml;
        resetButton.style.display = 'inline-flex';
        
        // Update confirm/reject buttons state
        updateButtonState();
        
    } catch (error) {
        similarityResults.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                An error occurred while making analysis: ${error.message}
            </div>
        `;
    }
}

async function analyzeDocument() {
    if (!isVideoRunning || currentObjectType !== 'document') return;
    
    similarityResults.innerHTML = `
        <div class="loading-container">
            <div class="loader"></div>
            <span>${getTranslation('documentAnalysisInProgress')}</span>
        </div>
    `;
    
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
        
        documentAnalysisResults = data;
        schoolNumber = data.student_no;
        
        let resultHtml = `
            <div class="document-analysis-results">
                <div class="result-item">
                    <h3>${getTranslation('documentInformation')}</h3>
                    ${data.student_no ? `<p>${getTranslation('studentNumber')}: <span class="score">${data.student_no}</span></p>` : ''}
                    ${data.name_surname ? `<p>${getTranslation('nameSurname')}: <span class="score">${data.name_surname}</span></p>` : ''}
                    ${data.department ? `<p>${getTranslation('department')}: <span class="score">${data.department}</span></p>` : ''}
                    ${data.class ? `<p>${getTranslation('class')}: <span class="score">${data.class}</span></p>` : ''}
                </div>
            </div>
        `;

        similarityResults.innerHTML = resultHtml;
        resetButton.style.display = 'inline-flex';

        // Öğrenci fotoğrafını bul ve göster
        await findStudent(similarityResults);

    } catch (error) {
        similarityResults.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                An error occurred while making analysis: ${error.message}
            </div>
        `;
    }
}

async function searchStudentByNumber(studentNumber) {
    if (!studentNumber) return;

    // Loading göster
    similarityResults.innerHTML = `
        <div class="loading-container">
            <div class="loader"></div>
            <span>${getTranslation('searching')}</span>
        </div>
    `;

    try {
        const response = await fetch('/find_student', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-School-Number': studentNumber
            }
        });

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
            <div class="document-analysis-results">
                <div class="result-item">
                    <h3>${getTranslation('studentInformation')}</h3>
                    <p>${getTranslation('studentNumber')}: <span class="score">${studentNumber}</span></p>
                </div>
                <div class="result-item">
                    <div class="student-image">
                        <img src="/get_student_image/${studentNumber}" alt="Student Image" 
                             style="width: 100px; height: 120px; object-fit: cover;">
                    </div>
                </div>
            </div>
        `;

        similarityResults.innerHTML = resultHtml;
        resetButton.disabled = false;
        resetButton.style.display = 'inline-flex';

    } catch (error) {
        similarityResults.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                ${getTranslation('searchError')}: ${error.message}
            </div>
        `;
    }
}

async function findStudent(similarityResults) {
    const currentContent = similarityResults.innerHTML;
    
    similarityResults.innerHTML += `
        <div id="loadingContainer" class="loading-container">
            <div class="loader"></div>
            <span>${getTranslation('searching')}</span>
        </div>
    `;
 
    try {
        if (!schoolNumber) {
            similarityResults.innerHTML += `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>${getTranslation('studentNotFound')}</p>
                </div>
            `;
            return;
        }
 
        const response = await fetch('/find_student', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-School-Number': schoolNumber
            }
        });
 
        const data = await response.json();
        
        if (data.error) {
            similarityResults.innerHTML += `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    ${data.error}
                </div>
            `;
            return;
        }
        
        let resultHtml = `
            <div class="result-item">
                <h3>${getTranslation('studentInformation')}</h3>
                <div class="student-image">
                    <img src="/get_student_image/${schoolNumber}" alt="Student Image" 
                         style="width: 100px; height: 120px; object-fit: cover;">
                </div>
            </div>
        `;
        
        similarityResults.innerHTML = currentContent + resultHtml;
 
    } catch (error) {
        similarityResults.innerHTML += `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                ${getTranslation('searchError')}: ${error.message}
            </div>
        `;
    } finally {
        const loadingContainer = document.getElementById('loadingContainer');
        if (loadingContainer) {
            loadingContainer.remove();
        }
    }
}

/* Document upload functions - Temporarily disabled
function previewImage(event) {
    const file = event.target.files[0];
    const preview = document.getElementById('imagePreview');
    const container = document.getElementById('imagePreviewContainer');
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            container.style.display = 'block';
        }
        reader.readAsDataURL(file);
    } else {
        container.style.display = 'none';
    }
}

async function uploadDocument() {
    const fileInput = document.getElementById('documentFile');
    
    if (!fileInput.files || !fileInput.files[0]) {
        showMessage('Please select a file first');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    similarityResults.innerHTML = `
        <div class="loading-container">
            <div class="loader"></div>
            <span>Analyzing uploaded document...</span>
        </div>
    `;

    try {
        const response = await fetch('/upload_document', {
            method: 'POST',
            body: formData
        });

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

        resetButton.disabled = false;
        documentAnalysisResults = data;
        schoolNumber = data.student_no;

        let resultHtml = `
            <div class="document-analysis-results">
                <div class="result-item">
                    <h3>Document Information</h3>
        `;

        if (data.student_no) resultHtml += `<p>Student Number: <span class="score">${data.student_no}</span></p>`;
        if (data.name_surname) resultHtml += `<p>Name Surname: <span class="score">${data.name_surname}</span></p>`;
        if (data.faculty) resultHtml += `<p>Faculty: <span class="score">${data.faculty}</span></p>`;
        if (data.department) resultHtml += `<p>Department: <span class="score">${data.department}</span></p>`;
        if (data.class) resultHtml += `<p>Class: <span class="score">${data.class}</span></p>`;

        resultHtml += `</div></div>`;
        similarityResults.innerHTML = resultHtml;

        if (schoolNumber) {
            await findStudent(similarityResults);
        }

    } catch (error) {
        similarityResults.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                Upload failed: ${error.message}
            </div>
        `;
    }
}
*/

// Exam Selection Functionality
document.addEventListener('DOMContentLoaded', function() {
    const examCheckboxes = document.querySelectorAll('.exam-checkbox');
    const selectAllCourse = document.querySelectorAll('.select-all-course');
    const selectAllExams = document.getElementById('selectAllExams');
    const clearAllExams = document.getElementById('clearAllExams');
    const selectedCount = document.getElementById('selectedCount');
    
    // Update selected count
    function updateSelectedCount() {
        const count = document.querySelectorAll('.exam-checkbox:checked').length;
        const lang = localStorage.getItem('preferredLanguage') || 'en';
        const suffix = selectedCount.getAttribute(`data-${lang}-prefix`) || '';
        selectedCount.textContent = `${count} ${suffix}`;
        
        // Export button should always be active
        const exportBtn = document.getElementById('exportExcelBtn');
        if(exportBtn) {
            exportBtn.disabled = false;
        }
    }
    
    // Handle individual checkbox changes
    examCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const course = this.getAttribute('data-course');
            const courseCheckboxes = document.querySelectorAll(`.exam-checkbox[data-course="${course}"]`);
            const courseSelectAll = document.querySelector(`.select-all-course[data-course="${course}"]`);
            
            // Check if all course checkboxes are checked
            const allChecked = Array.from(courseCheckboxes).every(cb => cb.checked);
            courseSelectAll.checked = allChecked;
            
            updateSelectedCount();
        });
    });
    
    // Handle "Select All" for a course
    selectAllCourse.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const course = this.getAttribute('data-course');
            const courseCheckboxes = document.querySelectorAll(`.exam-checkbox[data-course="${course}"]`);
            
            courseCheckboxes.forEach(cb => {
                cb.checked = this.checked;
            });
            
            updateSelectedCount();
        });
    });
    
    // Select All Exams
    selectAllExams.addEventListener('click', function() {
        examCheckboxes.forEach(checkbox => {
            checkbox.checked = true;
        });
        
        selectAllCourse.forEach(checkbox => {
            checkbox.checked = true;
        });
        
        updateSelectedCount();
    });
    
    // Clear All Exams
    clearAllExams.addEventListener('click', function() {
        examCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        
        selectAllCourse.forEach(checkbox => {
            checkbox.checked = false;
        });
        
        updateSelectedCount();
    });
    
    // Initialize count
    updateSelectedCount();
    
    // Make sure export button is always enabled
    const exportBtn = document.getElementById('exportExcelBtn');
    if(exportBtn) {
        exportBtn.disabled = false;
    }
    
    // Handle export button click
    document.getElementById('exportExcelBtn').addEventListener('click', function() {
        let selectedExams = Array.from(document.querySelectorAll('.exam-checkbox:checked'))
            .map(cb => cb.value);
            
        if(selectedExams.length === 0) {
            // Instead of showing a notification, silently select all exams and proceed
            const allExams = Array.from(document.querySelectorAll('.exam-checkbox'));
            selectedExams = allExams.map(cb => cb.value);
            
            // Proceed immediately with export without showing any message
            proceedWithExport(selectedExams);
        } else {
            proceedWithExport(selectedExams);
        }
    });
    
    // Helper function to handle the actual export process
    function proceedWithExport(selectedExams) {
        // Show loading in the results section
        similarityResults.innerHTML = `
            <div class="loading-container">
                <div class="loader"></div>
                <span>${getTranslation('generatingExcel')}</span>
            </div>
        `;
        
        // Send request to export the selected exams
        fetch('/export-to-excel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ exams: selectedExams })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(getTranslation('exportFailed'));
            }
            return response.blob();
        })
        .then(blob => {
            // Create a download link for the Excel file
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            const date = new Date().toISOString().split('T')[0];
            a.href = url;
            a.download = `attendance_export_${date}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            
            // Show success message with translation
            similarityResults.innerHTML = `
                <div class="success-message">
                    <i class="fas fa-check-circle"></i>
                    ${getTranslation('excelDownloaded')}
                </div>
            `;
            
            // Auto-hide Excel download success message after 3 seconds
            setTimeout(() => {
                similarityResults.innerHTML = `
                    <div class="result-item">
                        <p>${getTranslation('noAnalysis')}</p>
                    </div>
                `;
            }, 3000);
        })
        .catch(error => {
            similarityResults.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    ${getTranslation('exportFailed')}: ${error.message}
                </div>
            `;
        });
    }
});

// Exam dropdown toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    // Keep the existing exam checkbox functionality
    // ...existing code...
    
    // Add dropdown toggle functionality
    const examDropdownToggle = document.getElementById('examDropdownToggle');
    const examSelectionContent = document.getElementById('examSelectionContent');
    
    if (examDropdownToggle && examSelectionContent) {
        examDropdownToggle.setAttribute('aria-expanded', 'false');
        examDropdownToggle.addEventListener('click', function() {
            const expanded = this.getAttribute('aria-expanded') === 'true';
            this.setAttribute('aria-expanded', !expanded);
            
            if (expanded) {
                examSelectionContent.classList.remove('active');
            } else {
                examSelectionContent.classList.add('active');
            }
        });
    }
    
    // The rest of the existing exam checkbox functionality
    // ...existing code...
});

// Function to enable/disable buttons based on face analysis and course selection
function updateButtonState() {
    const hasSelectedCourse = document.querySelectorAll('.exam-checkbox:checked').length > 0;
    
    // Enable confirm/reject buttons only if face is analyzed and course is selected
    confirmButton.disabled = !(isFaceAnalyzed && hasSelectedCourse);
    rejectButton.disabled = !(isFaceAnalyzed && hasSelectedCourse);
}

// Function to handle confirm button click
function confirmAttendance() {
    if (!schoolNumber) {
        showMessage(getTranslation('noStudentSelected'));
        return;
    }

    // Get selected courses
    const selectedCourses = Array.from(document.querySelectorAll('.exam-checkbox:checked'))
        .map(cb => cb.value);
    
    if (selectedCourses.length === 0) {
        showMessage(getTranslation('selectCourse'));
        return;
    }

    // Prepare student data for saving
    const studentInfo = {
        schoolNumber: schoolNumber,
        courses: selectedCourses,
        timestamp: new Date().toISOString(),
        attendance: true
    };

    // Add document data if available
    if (documentAnalysisResults) {
        studentInfo.documentInfo = {
            nameSurname: documentAnalysisResults.name_surname || '',
            department: documentAnalysisResults.department || '',
            class: documentAnalysisResults.class || ''
        };
    }

    // Add face analysis data if available
    if (faceAnalysisResults) {
        studentInfo.faceAnalysis = faceAnalysisResults;
    }

    // Save student data to JSON file
    saveStudentData(studentInfo);
}

// Function to handle reject button click
function rejectAttendance() {
    if (!schoolNumber) {
        showMessage(getTranslation('noStudentSelected'));
        return;
    }
    
    // Reset the form without saving
    resetAnalysis();
    showMessage(getTranslation('attendanceRejected'));
}

// Function to clear all exam checkboxes
function clearExamSelections() {
    const examCheckboxes = document.querySelectorAll('.exam-checkbox');
    const selectAllCourse = document.querySelectorAll('.select-all-course');
    
    // Clear all exam checkboxes
    examCheckboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    
    // Clear all course "select all" checkboxes
    selectAllCourse.forEach(checkbox => {
        checkbox.checked = false;
    });
    
    // Update the selected count display with language support
    const selectedCount = document.getElementById('selectedCount');
    if (selectedCount) {
        const lang = localStorage.getItem('preferredLanguage') || 'en';
        const suffix = selectedCount.getAttribute(`data-${lang}-prefix`) || '';
        selectedCount.textContent = `0 ${suffix}`;
    }
}

// Function to save student data to a JSON file
async function saveStudentData(studentData) {
    similarityResults.innerHTML += `
        <div id="savingContainer" class="loading-container">
            <div class="loader"></div>
            <span>${getTranslation('savingAttendance')}</span>
        </div>
    `;

    try {
        const response = await fetch('/save_attendance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(studentData)
        });

        const data = await response.json();
        
        const savingContainer = document.getElementById('savingContainer');
        if (savingContainer) {
            savingContainer.remove();
        }

        if (data.error) {
            similarityResults.innerHTML += `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    ${data.error}
                </div>
            `;
        } else {
            similarityResults.innerHTML += `
                <div class="success-message">
                    <i class="fas fa-check-circle"></i>
                    ${getTranslation('attendanceSaved')}
                </div>
            `;
            
            // Clear the exam selections after successful save
            clearExamSelections();
            
            // Disable confirm/reject buttons after successful save
            confirmButton.disabled = true;
            rejectButton.disabled = true;
            
            // Reset after successful save
            setTimeout(() => {
                resetAnalysis();
            }, 2000);
        }
    } catch (error) {
        const savingContainer = document.getElementById('savingContainer');
        if (savingContainer) {
            savingContainer.remove();
        }

        similarityResults.innerHTML += `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                Error saving attendance: ${error.message}
            </div>
        `;
    }
}

// Add a language change event listener
document.addEventListener('DOMContentLoaded', function() {
    // ...existing code...
    
    // Listen for language changes and update dynamic content
    window.addEventListener('languageChanged', function(e) {
        // Update the selected count text when language changes
        const selectedCount = document.getElementById('selectedCount');
        if (selectedCount) {
            const count = document.querySelectorAll('.exam-checkbox:checked').length;
            const lang = localStorage.getItem('preferredLanguage') || 'en';
            const suffix = selectedCount.getAttribute(`data-${lang}-prefix`) || '';
            selectedCount.textContent = `${count} ${suffix}`;
        }
        
        // Update analysis results if they exist
        if (similarityResults.innerHTML.includes(getTranslation('studentInformation')) || 
            similarityResults.innerHTML.includes(getTranslation('documentInformation'))) {
            // If we have results displayed, refresh them with new language
            if (schoolNumber) {
                if (isFaceAnalyzed) {
                    analyzeFace();
                } else if (documentAnalysisResults) {
                    analyzeDocument();
                } else {
                    searchStudentByNumber(schoolNumber);
                }
            }
        }
    });
    
    // ...existing code...
});