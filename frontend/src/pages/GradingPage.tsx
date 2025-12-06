import { useMemo, useState } from 'react'
import { useAppStore } from '../store/app'
import BlockMath from '@matejmazur/react-katex'

export default function GradingPage() {
  const exams = useAppStore((s) => s.exams)
  const selectedExamId = useAppStore((s) => s.selectedExamId)
  const papers = useAppStore((s) => s.papers)
  const selectedPaperId = useAppStore((s) => s.selectedPaperId)
  const selectPaper = useAppStore((s) => s.selectPaper)
  const setManualScore = useAppStore((s) => s.setManualScore)
  const exam = useMemo(() => exams.find((e) => e.exam_id === selectedExamId) || exams[0], [exams, selectedExamId])
  const paper = useMemo(() => papers.filter((p) => p.exam_id === exam?.exam_id).find((p) => p.paper_id === selectedPaperId) || papers.filter((p) => p.exam_id === exam?.exam_id)[0], [papers, selectedPaperId, exam])
  const [qIndex, setQIndex] = useState(0)
  if (!exam || !paper) return <div className="card">请先上传试卷</div>
  const q = exam.questions[qIndex]
  const pq = paper.questions.find((x) => x.question_id === q.question_id)!
  const score = pq.manual_score ?? pq.ai_grading.score
  const onPrev = () => setQIndex((i) => Math.max(0, i - 1))
  const onNext = () => setQIndex((i) => Math.min(exam.questions.length - 1, i + 1))
  const onSave = () => setManualScore(paper.paper_id, q.question_id, score)
  return (
    <div className="row">
      <div className="side">
        {exam.questions.map((qq, i) => (
          <a key={qq.question_id} href="#" onClick={(e) => { e.preventDefault(); setQIndex(i) }} className={i === qIndex ? 'active' : ''}>Q{qq.question_id}</a>
        ))}
        <div style={{ marginTop: 12 }} className="list">
          {papers.map((p) => (
            <a key={p.paper_id} href="#" onClick={(e) => { e.preventDefault(); selectPaper(p.paper_id) }} className={p.paper_id === paper.paper_id ? 'active' : ''}>{p.test_code}</a>
          ))}
        </div>
      </div>
      <div className="card">
        <div className="title">题目 {q.question_id} 满分 {q.max_score}</div>
        <div className="muted" style={{ marginTop: 6 }}>标准答案</div>
        <div className="card" style={{ marginTop: 6 }}>
          <BlockMath math={q.correct_answer} />
        </div>
        <div className="images" style={{ marginTop: 12 }}>
          <img src={pq.solution_image_url} alt="solution" />
          <img src={pq.final_answer_image_url} alt="final" />
        </div>
        <div className="row" style={{ marginTop: 12 }}>
          <div className="field">
            <label>得分</label>
            <input type="number" min={0} max={q.max_score} step={0.5} value={score} onChange={(e) => setManualScore(paper.paper_id, q.question_id, Math.max(0, Math.min(q.max_score, Number(e.target.value))))} />
          </div>
          <div className="field">
            <label>AI 评语</label>
            <textarea rows={3} value={pq.ai_grading.explanation} readOnly />
          </div>
        </div>
        <div className="toolbar">
          <button className="btn" onClick={onPrev}>上一题</button>
          <button className="btn" onClick={onNext}>下一题</button>
          <button className="btn accent" onClick={onSave}>保存并继续</button>
        </div>
      </div>
    </div>
  )
}
