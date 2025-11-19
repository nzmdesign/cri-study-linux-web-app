// シンプルな一括送信用のクライアントスクリプト
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('exam-form');
    const submitBtn = document.getElementById('submit-btn');
    const totalQuestions = examData.questions.length;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // 回答を収集
        const answers = [];
        for (const q of examData.questions) {
            const name = `q-${q.id}`;
            const checked = form.querySelector(`input[name="${name}"]:checked`);
            if (checked) {
                answers.push({ question_id: q.id, selected_option: parseInt(checked.value, 10) });
            }
        }

        // 未回答チェック
        if (answers.length !== totalQuestions) {
            alert(`すべての問題に回答してください。（回答済み: ${answers.length}/${totalQuestions}）`);
            return;
        }

        // 送信中の表示
        submitBtn.disabled = true;
        submitBtn.textContent = '送信中...';

        try {
            // 一括送信
            const resp = await fetch(`/api/exam/${examId}/submit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ answers })
            });

            const result = await resp.json();

            if (result.redirect_url) {
                // 結果ページにリダイレクト
                window.location.href = result.redirect_url;
            } else {
                alert('結果の表示に失敗しました。');
                submitBtn.disabled = false;
                submitBtn.textContent = '送信';
            }

        } catch (err) {
            console.error('送信エラー', err);
            alert('送信中にエラーが発生しました。コンソールを確認してください。');
            submitBtn.disabled = false;
            submitBtn.textContent = '送信';
        }
    });
});

