document.addEventListener('DOMContentLoaded', function() {
    function toggleConfigSections() {
        const configMethod = document.querySelector('input[name="config_method"]:checked');
        const jsonFileSection = document.querySelector('.json-file-config');
        const jsonTextSection = document.querySelector('.json-text-config');
        
        if (configMethod) {
            if (configMethod.value === 'json_file') {
                if (jsonFileSection) jsonFileSection.style.display = 'block';
                if (jsonTextSection) jsonTextSection.style.display = 'none';
            } else if (configMethod.value === 'json_text') {
                if (jsonFileSection) jsonFileSection.style.display = 'none';
                if (jsonTextSection) jsonTextSection.style.display = 'block';
            }
        }
    }
    
    // 监听配置方式变化
    const configMethodRadios = document.querySelectorAll('input[name="config_method"]');
    configMethodRadios.forEach(radio => {
        radio.addEventListener('change', toggleConfigSections);
    });
    
    // 初始切换
    toggleConfigSections();
    
    // JSON验证功能
    const validateJsonBtn = document.createElement('button');
    validateJsonBtn.type = 'button';
    validateJsonBtn.textContent = '验证JSON格式';
    validateJsonBtn.className = 'button';
    validateJsonBtn.style.marginTop = '10px';
    
    const questionsField = document.getElementById('id_questions');
    if (questionsField) {
        questionsField.parentNode.appendChild(validateJsonBtn);
        
        validateJsonBtn.addEventListener('click', function() {
            try {
                const jsonData = JSON.parse(questionsField.value);
                alert('✅ JSON格式验证通过！');
            } catch (error) {
                alert('❌ JSON格式错误: ' + error.message);
            }
        });
    }
});