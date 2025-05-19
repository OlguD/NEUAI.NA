// Admin Panel JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Form elements
    const examForm = document.getElementById('examForm');
    const courseCodeInput = document.getElementById('courseCode');
    const examTypeSelect = document.getElementById('examType');
    const examDateInput = document.getElementById('examDate');
    const excelFileInput = document.getElementById('excelFile');
    const photoFilesInput = document.getElementById('photoFiles');
    const uploadAllBtn = document.getElementById('uploadAllBtn');
    const processingStatus = document.getElementById('processingStatus');
    const resultMessage = document.getElementById('resultMessage');
    const resultText = document.getElementById('resultText');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const excelPreviewTable = document.getElementById('excelPreviewTable');
    const photosGrid = document.getElementById('photosGrid');
    const selectedExcelFile = document.getElementById('selectedExcelFile');
    const selectedPhotoCount = document.getElementById('selectedPhotoCount');

    // Translations for messages
    const translations = {
        en: {
            examCreatedSuccess: "Exam created successfully!",
            examCreatedError: "Failed to create exam",
            selectExcelFirst: "Please select Excel file first",
            processingExcel: "Processing Excel file...",
            uploadingPhotos: "Uploading photos...",
            savingExam: "Saving exam data...",
            noStudentsFound: "No students found in Excel file",
            invalidExcelFormat: "Invalid Excel format. Please check your file.",
            examSaved: "Exam saved successfully!",
            photosMissing: "Please upload student photos",
            courseMissing: "Please enter course code",
            examTypeMissing: "Please select exam type",
            dateMissing: "Please select exam date",
            // Column headers for different formats
            studentId: "Student ID",
            name: "Name",
            surname: "Surname",
            fullName: "Full Name",
            faculty: "Faculty",
            department: "Department",
            status: "Status",
            excelFormat1Detected: "Format 1 detected: 'Öğrenci No', 'Ad', 'Soyad'",
            excelFormat2Detected: "Format 2 detected: 'Resim', 'Öğrenci No', 'Ad Soyad', 'Fakülte', 'Bölüm', 'Durum'"
        },
        tr: {
            examCreatedSuccess: "Sınav başarıyla oluşturuldu!",
            examCreatedError: "Sınav oluşturulamadı",
            selectExcelFirst: "Lütfen önce Excel dosyasını seçin",
            processingExcel: "Excel dosyası işleniyor...",
            uploadingPhotos: "Fotoğraflar yükleniyor...",
            savingExam: "Sınav verileri kaydediliyor...",
            noStudentsFound: "Excel dosyasında öğrenci bulunamadı",
            invalidExcelFormat: "Geçersiz Excel formatı. Lütfen dosyanızı kontrol edin.",
            examSaved: "Sınav başarıyla kaydedildi!",
            photosMissing: "Lütfen öğrenci fotoğraflarını yükleyin",
            courseMissing: "Lütfen ders kodunu girin",
            examTypeMissing: "Lütfen sınav türünü seçin",
            dateMissing: "Lütfen sınav tarihini seçin",
            // Column headers for different formats
            studentId: "Öğrenci No",
            name: "Ad",
            surname: "Soyad",
            fullName: "Ad Soyad",
            faculty: "Fakülte",
            department: "Bölüm",
            status: "Durum",
            excelFormat1Detected: "Format 1 algılandı: 'Öğrenci No', 'Ad', 'Soyad'",
            excelFormat2Detected: "Format 2 algılandı: 'Resim', 'Öğrenci No', 'Ad Soyad', 'Fakülte', 'Bölüm', 'Durum'"
        }
    };

    // Get translation based on current language
    function getTranslation(key) {
        const lang = localStorage.getItem('preferredLanguage') || 'en';
        return translations[lang][key] || key;
    }

    // Excel file parsing - using xlsx.js (need to include it in HTML)
    excelFileInput?.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) return;

        // Update selected file display
        selectedExcelFile.textContent = file.name;
        
        // Remove any existing format notice
        const existingNotice = document.querySelector('.format-notice');
        if (existingNotice) {
            existingNotice.remove();
        }

        // Parse Excel file with SheetJS (xlsx)
        if (typeof XLSX === 'undefined') {
            console.error('XLSX library not loaded');
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const data = new Uint8Array(e.target.result);
                const workbook = XLSX.read(data, {type: 'array'});
                const firstSheet = workbook.SheetNames[0];
                const worksheet = workbook.Sheets[firstSheet];
                const jsonData = XLSX.utils.sheet_to_json(worksheet);

                if (jsonData.length === 0) {
                    excelPreviewTable.innerHTML = `
                        <tr class="empty-row">
                            <td colspan="3">${getTranslation('noStudentsFound')}</td>
                        </tr>
                    `;
                    return;
                }

                // Validate schema for both supported formats
                const firstRow = jsonData[0];
                
                // Detect the format type based on column headers
                let formatType = null;
                
                const columnKeys = Object.keys(firstRow);
                
                // Format 2: "Resim", "Öğrenci No", "Ad Soyad", "Fakülte", "Bölüm", "Durum"
                if (
                    columnKeys.includes('Öğrenci No') && 
                    columnKeys.includes('Ad Soyad') && 
                    columnKeys.includes('Fakülte') && 
                    columnKeys.includes('Bölüm') && 
                    columnKeys.includes('Durum')
                ) {
                    formatType = 'format2';
                }
                // Format 1: "Öğrenci No", "Ad", "Soyad"
                else if (
                    columnKeys.includes('Öğrenci No') && 
                    columnKeys.includes('Ad') && 
                    columnKeys.includes('Soyad')
                ) {
                    formatType = 'format1';
                }
                
                // Store the format type for later use
                if (excelPreviewTable) {
                    excelPreviewTable.dataset.formatType = formatType;
                }
                
                const hasRequiredFields = (formatType === 'format1' || formatType === 'format2');

                if (!hasRequiredFields) {
                    excelPreviewTable.innerHTML = `
                        <tr class="empty-row">
                            <td colspan="3">${getTranslation('invalidExcelFormat')}</td>
                        </tr>
                    `;
                    return;
                }

                // Display preview in table
                const currentFormatType = excelPreviewTable.dataset.formatType;
                
                // Set table headers based on format type
                let tableHeaders = '';
                if (currentFormatType === 'format2') {
                    tableHeaders = `<th>${getTranslation('studentId')}</th><th>${getTranslation('name')}</th><th>${getTranslation('surname')}</th>`;
                    
                    // Add notification about format detection
                    const formatNotice = document.createElement('div');
                    formatNotice.className = 'format-notice';
                    formatNotice.textContent = getTranslation('excelFormat2Detected');
                    formatNotice.style.color = '#4caf50';
                    formatNotice.style.marginBottom = '10px';
                    formatNotice.style.fontStyle = 'italic';
                    formatNotice.style.fontWeight = 'bold';
                    
                    // Insert before the table
                    excelPreviewTable.parentNode.insertBefore(formatNotice, excelPreviewTable);
                } else {
                    // Default format1 headers
                    tableHeaders = `<th>${getTranslation('studentId')}</th><th>${getTranslation('name')}</th><th>${getTranslation('surname')}</th>`;
                    
                    // Add notification about format detection if it's format1
                    if (currentFormatType === 'format1') {
                        const formatNotice = document.createElement('div');
                        formatNotice.className = 'format-notice';
                        formatNotice.textContent = getTranslation('excelFormat1Detected');
                        formatNotice.style.color = '#2196F3';
                        formatNotice.style.marginBottom = '10px';
                        formatNotice.style.fontStyle = 'italic';
                        
                        // Insert before the table
                        excelPreviewTable.parentNode.insertBefore(formatNotice, excelPreviewTable);
                    }
                }
                
                let tableHTML = `<thead><tr>${tableHeaders}</tr></thead><tbody>`;
                
                jsonData.slice(0, 10).forEach(row => {
                    let studentId = '';
                    let name = '';
                    let surname = '';
                    
                    if (currentFormatType === 'format1') {
                        // Format 1: "Öğrenci No", "Ad", "Soyad"
                        studentId = row['Öğrenci No'] || '';
                        name = row['Ad'] || '';
                        surname = row['Soyad'] || '';
                    } 
                    else if (currentFormatType === 'format2') {
                        // Format 2: "Resim", "Öğrenci No", "Ad Soyad", "Fakülte", "Bölüm", "Durum"
                        studentId = row['Öğrenci No'] || '';
                        
                        // Handle "Ad Soyad" (Full Name) by splitting it into name and surname
                        const fullName = row['Ad Soyad'] || '';
                        if (fullName) {
                            const nameParts = fullName.trim().split(' ');
                            if (nameParts.length > 1) {
                                // Last part is surname, everything else is name
                                surname = nameParts.pop();
                                name = nameParts.join(' ');
                            } else if (nameParts.length === 1) {
                                name = nameParts[0];
                                surname = '';
                            }
                        }
                    }
                    else {
                        // Fallback for unknown format - try to match expected Turkish or English field names
                        studentId = 
                            row['Öğrenci No'] || 
                            row['Student ID'] || 
                            row['StudentID'] || 
                            row['ID'] || 
                            '';
                        
                        // Try to find name and surname fields
                        if (row['Ad'] && row['Soyad']) {
                            // Format 1 style fields
                            name = row['Ad'] || '';
                            surname = row['Soyad'] || '';
                        } 
                        else if (row['Ad Soyad']) {
                            // Format 2 style combined name field
                            const fullName = row['Ad Soyad'] || '';
                            const nameParts = fullName.trim().split(' ');
                            if (nameParts.length > 1) {
                                surname = nameParts.pop();
                                name = nameParts.join(' ');
                            } else {
                                name = fullName;
                                surname = '';
                            }
                        }
                        else {
                            // Try English fields
                            name = row['Name'] || row['First Name'] || '';
                            surname = row['Surname'] || row['Last Name'] || '';
                        }
                    }
                    
                    tableHTML += `<tr>
                        <td>${studentId}</td>
                        <td>${name}</td>
                        <td>${surname}</td>
                    </tr>`;
                });

                // If there are more rows, add a message
                if (jsonData.length > 10) {
                    tableHTML += `<tr>
                        <td colspan="3" style="text-align: center; font-style: italic;">
                            ... and ${jsonData.length - 10} more students
                        </td>
                    </tr>`;
                }
                
                tableHTML += '</tbody>';
                excelPreviewTable.innerHTML = tableHTML;
                
                // Store the parsed data in a hidden field or as a dataset attribute for later use
                excelPreviewTable.dataset.students = JSON.stringify(jsonData);
                
                // Enable the upload button if all fields are filled
                checkFormValidity();
            } catch (error) {
                console.error('Error parsing Excel file:', error);
                excelPreviewTable.innerHTML = `
                    <tr class="empty-row">
                        <td colspan="3">Error parsing file: ${error.message}</td>
                    </tr>
                `;
            }
        };
        reader.readAsArrayBuffer(file);
    });

    // Photo files preview
    photoFilesInput?.addEventListener('change', function(e) {
        const files = Array.from(e.target.files);
        if (files.length === 0) return;

        // Update the selected files count
        selectedPhotoCount.textContent = files.length === 1 
            ? '1 file chosen' 
            : `${files.length} files chosen`;

        // Clear the current photos grid
        photosGrid.innerHTML = '';

        // Preview first 12 photos
        const maxPreview = Math.min(files.length, 12);
        for (let i = 0; i < maxPreview; i++) {
            const file = files[i];
            if (!file.type.match('image.*')) continue;

            const reader = new FileReader();
            reader.onload = function(e) {
                const photoItem = document.createElement('div');
                photoItem.className = 'photo-item';
                
                // Extract the file name without extension
                const fileName = file.name.split('.')[0];
                
                photoItem.innerHTML = `
                    <img src="${e.target.result}" alt="Student photo">
                    <span class="photo-name">${fileName}</span>
                `;
                photosGrid.appendChild(photoItem);
            };
            reader.readAsDataURL(file);
        }

        // If there are more photos than the preview limit
        if (files.length > maxPreview) {
            const morePhotos = document.createElement('div');
            morePhotos.className = 'photo-item more-photos';
            morePhotos.innerHTML = `+${files.length - maxPreview} more`;
            photosGrid.appendChild(morePhotos);
        }
        
        // Enable the upload button if all fields are filled
        checkFormValidity();
    });

    // Form validation
    function checkFormValidity() {
        const courseCode = courseCodeInput?.value.trim();
        const examType = examTypeSelect?.value;
        const examDate = examDateInput?.value;
        const hasExcel = excelFileInput?.files.length > 0;
        const hasPhotos = photoFilesInput?.files.length > 0;
        
        const isValid = courseCode && examType && examDate && hasExcel && hasPhotos;
        if (uploadAllBtn) {
            uploadAllBtn.disabled = !isValid;
        }
        
        return isValid;
    }

    // Add input event listeners to all form fields for validation
    [courseCodeInput, examTypeSelect, examDateInput].forEach(element => {
        element?.addEventListener('input', checkFormValidity);
        element?.addEventListener('change', checkFormValidity);
    });

    // Form submission handler
    uploadAllBtn?.addEventListener('click', async function(e) {
        e.preventDefault();
        
        if (!checkFormValidity()) {
            // Show specific error messages for missing fields
            if (!courseCodeInput.value.trim()) {
                showErrorMessage(getTranslation('courseMissing'));
                return;
            }
            if (!examTypeSelect.value) {
                showErrorMessage(getTranslation('examTypeMissing'));
                return;
            }
            if (!examDateInput.value) {
                showErrorMessage(getTranslation('dateMissing'));
                return;
            }
            if (excelFileInput.files.length === 0) {
                showErrorMessage(getTranslation('selectExcelFirst'));
                return;
            }
            if (photoFilesInput.files.length === 0) {
                showErrorMessage(getTranslation('photosMissing'));
                return;
            }
            return;
        }
        
        // Hide any previous result messages
        resultMessage.style.display = 'none';
        
        // Show processing status
        processingStatus.style.display = 'block';
        updateProgress(5, getTranslation('processingExcel'));
        
        try {
            // 1. Get the parsed Excel data
            const studentsData = JSON.parse(excelPreviewTable.dataset.students || '[]');
            
            if (studentsData.length === 0) {
                updateProgress(0, getTranslation('noStudentsFound'));
                return;
            }
            
            // 2. Process and standardize student data
            updateProgress(20, getTranslation('processingExcel'));
            
            // Determine the format type from the dataset
            const formatType = excelPreviewTable.dataset.formatType || 'format1';
            
            const processedStudents = studentsData.map(row => {
                let studentId = '';
                let name = '';
                let surname = '';
                
                if (formatType === 'format1') {
                    // Format 1: "Öğrenci No", "Ad", "Soyad"
                    studentId = row['Öğrenci No'] || '';
                    name = row['Ad'] || '';
                    surname = row['Soyad'] || '';
                } 
                else if (formatType === 'format2') {
                    // Format 2: "Resim", "Öğrenci No", "Ad Soyad", "Fakülte", "Bölüm", "Durum"
                    studentId = row['Öğrenci No'] || '';
                    
                    // Handle "Ad Soyad" (Full Name) by splitting it into name and surname
                    const fullName = row['Ad Soyad'] || '';
                    if (fullName) {
                        const nameParts = fullName.trim().split(' ');
                        if (nameParts.length > 1) {
                            // Last part is surname, everything else is name
                            surname = nameParts.pop();
                            name = nameParts.join(' ');
                        } else if (nameParts.length === 1) {
                            name = nameParts[0];
                            surname = '';
                        }
                    }
                    
                    // Store additional information
                    const faculty = row['Fakülte'] || '';
                    const department = row['Bölüm'] || '';
                    const status = row['Durum'] || '';
                }
                else {
                    // Fallback for unknown format - try to match expected Turkish or English field names
                    studentId = 
                        row['Öğrenci No'] || 
                        row['Student ID'] || 
                        row['StudentID'] || 
                        row['ID'] || 
                        '';
                    
                    // Try to find name and surname fields
                    if (row['Ad'] && row['Soyad']) {
                        // Format 1 style fields
                        name = row['Ad'] || '';
                        surname = row['Soyad'] || '';
                    } 
                    else if (row['Ad Soyad']) {
                        // Format 2 style combined name field
                        const fullName = row['Ad Soyad'] || '';
                        const nameParts = fullName.trim().split(' ');
                        if (nameParts.length > 1) {
                            surname = nameParts.pop();
                            name = nameParts.join(' ');
                        } else {
                            name = fullName;
                            surname = '';
                        }
                    }
                    else {
                        // Try English fields
                        name = row['Name'] || row['First Name'] || '';
                        surname = row['Surname'] || row['Last Name'] || '';
                    }
                }
                
                // Build the student object with the basic required fields
                let studentObj = {
                    id: studentId.toString(),
                    name: name,
                    surname: surname
                };
                
                // Add additional fields if format2 and they exist
                if (formatType === 'format2') {
                    const faculty = row['Fakülte'] || '';
                    const department = row['Bölüm'] || '';
                    const status = row['Durum'] || '';
                    
                    if (faculty) studentObj.faculty = faculty;
                    if (department) studentObj.department = department;
                    if (status) studentObj.status = status;
                }
                
                return studentObj;
            });
            
            // 3. Upload student photos
            updateProgress(40, getTranslation('uploadingPhotos'));
            
            // In a real app, you would upload photos to server here
            // For this prototype, we'll just simulate progress
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // 4. Prepare exam data
            updateProgress(70, getTranslation('savingExam'));
            
            const examData = {
                courseCode: courseCodeInput.value.trim(),
                examType: examTypeSelect.value,
                examDate: examDateInput.value,
                students: processedStudents,
                totalStudents: processedStudents.length,
                createdAt: new Date().toISOString()
            };
            
            // 5. Save exam data
            updateProgress(85, getTranslation('savingExam'));
            
            const response = await fetch('/save_exam', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(examData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Show success message
                updateProgress(100, getTranslation('examSaved'));
                setTimeout(() => {
                    processingStatus.style.display = 'none';
                    resultMessage.style.display = 'block';
                    resultText.textContent = getTranslation('examCreatedSuccess');
                }, 500);
                
                // Reset form after successful submission
                resetForm();
            } else {
                throw new Error(result.error || 'Unknown error');
            }
            
        } catch (error) {
            console.error('Error creating exam:', error);
            processingStatus.style.display = 'none';
            showErrorMessage(getTranslation('examCreatedError') + ': ' + error.message);
        }
    });

    // Helper function to update progress bar and text
    function updateProgress(percent, message) {
        if (progressBar) progressBar.style.width = `${percent}%`;
        if (progressText) progressText.textContent = `${percent}%`;
        
        // Update the processing message if provided
        const processingMessage = document.querySelector('#processingStatus .loading-container span');
        if (processingMessage && message) {
            processingMessage.textContent = message;
        }
    }

    // Helper function to show error messages
    function showErrorMessage(message) {
        resultMessage.style.display = 'block';
        const resultMessageDiv = document.querySelector('#resultMessage .success-message');
        if (resultMessageDiv) {
            resultMessageDiv.className = 'error-message';
            resultMessageDiv.innerHTML = `
                <i class="fas fa-exclamation-circle"></i>
                <span>${message}</span>
            `;
        }
    }

    // Reset form after successful submission
    function resetForm() {
        if (examForm) examForm.reset();
        if (excelPreviewTable) {
            excelPreviewTable.innerHTML = `
                <thead>
                    <tr>
                        <th data-en="Student ID" data-tr="Öğrenci No">Student ID</th>
                        <th data-en="Name" data-tr="Ad">Name</th>
                        <th data-en="Surname" data-tr="Soyad">Surname</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="empty-row">
                        <td colspan="3" data-en="Excel preview will appear here" data-tr="Excel önizlemesi burada görünecek">
                            Excel preview will appear here
                        </td>
                    </tr>
                </tbody>
            `;
            // Clear stored data and format type
            delete excelPreviewTable.dataset.students;
            delete excelPreviewTable.dataset.formatType;
            
            // Remove any format notice if present
            const formatNotice = document.querySelector('.format-notice');
            if (formatNotice) {
                formatNotice.remove();
            }
        }
        
        if (photosGrid) {
            photosGrid.innerHTML = `
                <div class="empty-photos" data-en="Photo previews will appear here" data-tr="Fotoğraf önizlemeleri burada görünecek">
                    Photo previews will appear here
                </div>
            `;
        }
        
        if (selectedExcelFile) selectedExcelFile.textContent = document.documentElement.lang === 'tr' ? 'Dosya seçilmedi' : 'No file chosen';
        if (selectedPhotoCount) selectedPhotoCount.textContent = document.documentElement.lang === 'tr' ? 'Dosya seçilmedi' : 'No files chosen';
        
        if (uploadAllBtn) uploadAllBtn.disabled = true;
        
        // Update the language for reset elements
        const lang = localStorage.getItem('preferredLanguage') || 'en';
        document.querySelectorAll('[data-en][data-tr]').forEach(element => {
            element.textContent = element.getAttribute(`data-${lang}`);
        });
    }

    // Initialize form validation on page load
    checkFormValidity();
});
