import { useMemo, useState } from 'react'
import { Exam } from '../types'
import { useAppStore } from '../store/app'
import { saveExam } from '../api'
import { Tabs, Tab, Button, TextField, Typography, Box, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material'
import { deleteExam } from '../api'

export default function ExamConfigPage() {
  const exams = useAppStore((s) => s.exams)
  const selectedExamId = useAppStore((s) => s.selectedExamId)
  const selectExam = useAppStore((s) => s.selectExam)
  const updateExam = useAppStore((s) => s.updateExam)
  const addExam = useAppStore((s) => s.addExam)
  const removeExam = useAppStore((s) => s.removeExam)
  const current = useMemo(() => exams.find((e) => e.exam_id === selectedExamId) || exams[0] || null, [exams, selectedExamId])
  const [mode, setMode] = useState<'view' | 'create'>('view')
  const [draft, setDraft] = useState<Exam | null>(current)
  const [newExam, setNewExam] = useState<Exam>({ exam_id: '', title: '', total_questions: 0, created_at: new Date().toISOString(), questions: [] })
  const [newCount, setNewCount] = useState<number>(0)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [deleteText, setDeleteText] = useState('')
  const onAddQuestion = () => {
    if (!draft) return
    const nextId = (draft.questions[draft.questions.length - 1]?.question_id || 0) + 1
    const q = {
      question_id: nextId,
      max_score: 1,
      correct_answer: '',
      solution_page: 1,
      final_answer_page: 1,
      rubrics: [
        { rubric_title: 'Default', rubric_template: '评分说明：\n- 对比 {solution} 与 {correct_answer}\n- 最终答案 {final_answer} 是否一致\n- 满分 {max_score}，小错误适当扣分' }
      ]
    }
    const updatedQuestions = [...draft.questions, q]
    const total_images = 2 * updatedQuestions.length + 1
    setDraft({ ...draft, total_questions: draft.total_questions + 1, questions: updatedQuestions, total_images })
  }
  const onSave = () => {
    if (!draft) return
    (async () => {
      const payload = { ...draft, total_images: draft.total_images ?? (2 * draft.questions.length + 1) }
      const saved = await saveExam(payload as Exam)
      updateExam(saved)
      selectExam(saved.exam_id)
    })()
  }
  const onCreateGenerate = (count: number) => {
    const qs = Array.from({ length: count }, (_, i) => ({
      question_id: i + 1,
      max_score: 5,
      correct_answer: '',
      solution_page: 1,
      final_answer_page: 1,
      rubrics: [
        { rubric_title: '默认模板', rubric_template: '评分说明：\n- 对比 {solution} 与 {correct_answer}\n- 最终答案 {final_answer} 是否一致\n- 满分 {max_score}，小错误适当扣分' }
      ]
    }))
    setNewExam({ ...newExam, total_questions: count, questions: qs, total_images: 2 * count + 1 })
  }
  const onCreateSave = () => {
    (async () => {
      const payload = { ...newExam, created_at: new Date().toISOString() }
      const saved = await saveExam({ ...payload, total_images: payload.total_images ?? (2 * payload.questions.length + 1) } as Exam)
      addExam(saved)
      selectExam(saved.exam_id)
      setMode('view')
      setDraft(saved)
    })()
  }
  return (
    <div className="row">
      <div className="card">
        <div className="title">考试页面</div>
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mt: 1 }}>
          <Tabs value={mode === 'view' ? 0 : 1} onChange={(_, v) => { setMode(v === 0 ? 'view' : 'create'); if (v === 0) setDraft(current) }}>
            <Tab label="查看已配置" />
            <Tab label="新增考试" />
          </Tabs>
        </Box>
      </div>
      {mode === 'view' && draft && (
        <>
          <div className="card">
          <div className="grid-3" style={{ marginTop: 8 }}>
              <div className="field">
                <label>考试</label>
                <select value={draft.exam_id} onChange={(e) => {
                  const exam = exams.find((x) => x.exam_id === e.target.value)
                  if (exam) { setDraft(exam); selectExam(exam.exam_id) }
                }}>
                  {exams.map((e) => (
                    <option key={e.exam_id} value={e.exam_id}>{e.title}</option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label>标题</label>
                <TextField value={draft.title} onChange={(e) => setDraft({ ...draft, title: e.target.value })} size="small" />
              </div>
              <div className="field">
                <label>试题数量</label>
                <TextField type="number" value={draft.total_questions} onChange={(e) => setDraft({ ...draft, total_questions: Number(e.target.value) })} size="small" />
              </div>
              <div className="field">
                <label>总图片数</label>
                <TextField type="number" value={draft.total_images ?? (2 * draft.questions.length + 1)} onChange={(e) => setDraft({ ...draft, total_images: Number(e.target.value) })} size="small" />
              </div>
            </div>
            <div className="btnbar" style={{ marginTop: 8 }}>
              <Button variant="outlined" onClick={onAddQuestion}>添加题目</Button>
              <Button variant="contained" onClick={onSave}>保存考试</Button>
              <Button color="error" onClick={() => { setDeleteOpen(true); setDeleteText('') }}>删除考试</Button>
            </div>
          </div>
          <div className="card">
            <div className="title">题目列表</div>
            <div className="muted" style={{ marginTop: 6 }}>当前共有 {draft.questions.length} 道题</div>
            <div className="list" style={{ marginTop: 8 }}>
              {draft.questions.map((q, idx) => (
                <div key={q.question_id} className="card" style={{ padding: 12 }}>
                  <div className="badge">Q{q.question_id}</div>
                  <div className="grid-3" style={{ marginTop: 8 }}>
                    <div className="field">
                      <label>满分</label>
                      <TextField type="number" value={q.max_score} onChange={(e) => {
                        const n = Number(e.target.value)
                        const qs = [...draft.questions]
                        qs[idx] = { ...q, max_score: n }
                        setDraft({ ...draft, questions: qs })
                      }} size="small" />
                    </div>
                    <div className="field">
                      <label>解答页码</label>
                      <TextField type="number" value={q.solution_page} onChange={(e) => {
                        const n = Number(e.target.value)
                        const qs = [...draft.questions]
                        qs[idx] = { ...q, solution_page: n }
                        setDraft({ ...draft, questions: qs })
                      }} size="small" />
                    </div>
                    <div className="field">
                      <label>最终答案页码</label>
                      <TextField type="number" value={q.final_answer_page} onChange={(e) => {
                        const n = Number(e.target.value)
                        const qs = [...draft.questions]
                        qs[idx] = { ...q, final_answer_page: n }
                        setDraft({ ...draft, questions: qs })
                      }} size="small" />
                    </div>
                  </div>
                  <div className="field" style={{ marginTop: 8 }}>
                    <label>标准答案 (LaTeX 支持)</label>
                    <TextField value={q.correct_answer} onChange={(e) => {
                      const qs = [...draft.questions]
                      qs[idx] = { ...q, correct_answer: e.target.value }
                      setDraft({ ...draft, questions: qs })
                    }} size="small" />
                  </div>
                  <div className="list" style={{ marginTop: 8 }}>
                    {q.rubrics.map((rb, rIdx) => (
                      <div key={rIdx} className="card" style={{ padding: 10 }}>
                        <div className="grid-3">
                          <div className="field">
                            <label>模板标题</label>
                            <TextField value={rb.rubric_title} onChange={(e) => {
                              const qs = [...draft.questions]
                              const rubrics = [...q.rubrics]
                              rubrics[rIdx] = { ...rb, rubric_title: e.target.value }
                              qs[idx] = { ...q, rubrics }
                              setDraft({ ...draft, questions: qs })
                            }} size="small" />
                          </div>
                          <div className="field" style={{ gridColumn: 'span 2' }}>
                            <label>评分模板</label>
                            <TextField multiline rows={3} value={rb.rubric_template} onChange={(e) => {
                              const qs = [...draft.questions]
                              const rubrics = [...q.rubrics]
                              rubrics[rIdx] = { ...rb, rubric_template: e.target.value }
                              qs[idx] = { ...q, rubrics }
                              setDraft({ ...draft, questions: qs })
                            }} size="small" />
                            <Typography variant="caption" className="muted" sx={{ display: 'block', mt: 0.5 }}>可用替代符：{`{solution}`}、{`{final_answer}`}、{`{correct_answer}`}、{`{max_score}`}</Typography>
                          </div>
                        </div>
                        <div className="btnbar" style={{ marginTop: 8 }}>
                          <Button variant="outlined" onClick={() => {
                            const qs = [...draft.questions]
                            const rubrics = q.rubrics.filter((_, i) => i !== rIdx)
                            qs[idx] = { ...q, rubrics }
                            setDraft({ ...draft, questions: qs })
                          }}>删除模板</Button>
                          <Button variant="text" onClick={() => {
                            const qs = [...draft.questions]
                            const rubrics = [...q.rubrics, { rubric_title: '新增模板', rubric_template: '评分说明：\n- 对比 {solution} 与 {correct_answer}\n- 最终答案 {final_answer} 是否一致\n- 满分 {max_score}，小错误适当扣分' }]
                            qs[idx] = { ...q, rubrics }
                            setDraft({ ...draft, questions: qs })
                          }}>新增模板</Button>
                        </div>
                      </div>
                    ))}
                    {q.rubrics.length === 0 && (
                      <Button variant="outlined" onClick={() => {
                        const qs = [...draft.questions]
                        const rubrics = [{ rubric_title: '默认模板', rubric_template: '评分说明：\n- 对比 {solution} 与 {correct_answer}\n- 最终答案 {final_answer} 是否一致\n- 满分 {max_score}，小错误适当扣分' }]
                        qs[idx] = { ...q, rubrics }
                        setDraft({ ...draft, questions: qs })
                      }}>添加模板</Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
      {mode === 'create' && (
        <>
          <div className="card">
            <div className="grid-3" style={{ marginTop: 8 }}>
              <div className="field">
                <label>标题</label>
                <TextField value={newExam.title} onChange={(e) => setNewExam({ ...newExam, title: e.target.value })} size="small" />
              </div>
              <div className="field">
                <label>题目数量</label>
                <TextField type="number" value={newCount} onChange={(e) => { const c = Math.max(0, Number(e.target.value)); setNewCount(c); onCreateGenerate(c) }} size="small" />
              </div>
              <div className="field">
                <label>总图片数</label>
                <TextField type="number" value={newExam.total_images ?? (2 * newExam.questions.length + 1)} onChange={(e) => setNewExam({ ...newExam, total_images: Number(e.target.value) })} size="small" />
              </div>
            </div>
            <div className="btnbar" style={{ marginTop: 8 }}>
              <Button variant="contained" onClick={onCreateSave}>保存考试</Button>
            </div>
          </div>
          <div className="card">
            <div className="title">题目列表</div>
            <div className="muted" style={{ marginTop: 6 }}>当前共有 {newExam.questions.length} 道题</div>
            <div className="list" style={{ marginTop: 8 }}>
              {newExam.questions.map((q, idx) => (
                <div key={q.question_id} className="card" style={{ padding: 12 }}>
                  <div className="badge">Q{q.question_id}</div>
                  <div className="grid-3" style={{ marginTop: 8 }}>
                    <div className="field">
                      <label>满分</label>
                      <TextField type="number" value={q.max_score} onChange={(e) => {
                        const n = Number(e.target.value)
                        const qs = [...newExam.questions]
                        qs[idx] = { ...q, max_score: n }
                        setNewExam({ ...newExam, questions: qs })
                      }} size="small" />
                    </div>
                    <div className="field">
                      <label>解答页码</label>
                      <TextField type="number" value={q.solution_page} onChange={(e) => {
                        const n = Number(e.target.value)
                        const qs = [...newExam.questions]
                        qs[idx] = { ...q, solution_page: n }
                        setNewExam({ ...newExam, questions: qs })
                      }} size="small" />
                    </div>
                    <div className="field">
                      <label>最终答案页码</label>
                      <TextField type="number" value={q.final_answer_page} onChange={(e) => {
                        const n = Number(e.target.value)
                        const qs = [...newExam.questions]
                        qs[idx] = { ...q, final_answer_page: n }
                        setNewExam({ ...newExam, questions: qs })
                      }} size="small" />
                    </div>
                  </div>
                  <div className="field" style={{ marginTop: 8 }}>
                    <label>标准答案</label>
                    <TextField value={q.correct_answer} onChange={(e) => {
                      const qs = [...newExam.questions]
                      qs[idx] = { ...q, correct_answer: e.target.value }
                      setNewExam({ ...newExam, questions: qs })
                    }} size="small" />
                  </div>
                  <div className="list" style={{ marginTop: 8 }}>
                    {q.rubrics.map((rb, rIdx) => (
                      <div key={rIdx} className="card" style={{ padding: 10 }}>
                        <div className="grid-3">
                          <div className="field">
                            <label>模板标题</label>
                            <TextField value={rb.rubric_title} onChange={(e) => {
                              const qs = [...newExam.questions]
                              const rubrics = [...q.rubrics]
                              rubrics[rIdx] = { ...rb, rubric_title: e.target.value }
                              qs[idx] = { ...q, rubrics }
                              setNewExam({ ...newExam, questions: qs })
                            }} size="small" />
                          </div>
                          <div className="field" style={{ gridColumn: 'span 2' }}>
                            <label>评分模板</label>
                            <TextField multiline rows={3} value={rb.rubric_template} onChange={(e) => {
                              const qs = [...newExam.questions]
                              const rubrics = [...q.rubrics]
                              rubrics[rIdx] = { ...rb, rubric_template: e.target.value }
                              qs[idx] = { ...q, rubrics }
                              setNewExam({ ...newExam, questions: qs })
                            }} size="small" />
                            <Typography variant="caption" className="muted" sx={{ display: 'block', mt: 0.5 }}>可用替代符：{`{solution}`}、{`{final_answer}`}、{`{correct_answer}`}、{`{max_score}`}</Typography>
                          </div>
                        </div>
                        <div className="btnbar" style={{ marginTop: 8 }}>
                          <Button variant="outlined" onClick={() => {
                            const qs = [...newExam.questions]
                            const rubrics = q.rubrics.filter((_, i) => i !== rIdx)
                            qs[idx] = { ...q, rubrics }
                            setNewExam({ ...newExam, questions: qs })
                          }}>删除模板</Button>
                          <Button variant="text" onClick={() => {
                            const qs = [...newExam.questions]
                            const rubrics = [...q.rubrics, { rubric_title: '新增模板', rubric_template: '评分说明：\n- 对比 {solution} 与 {correct_answer}\n- 最终答案 {final_answer} 是否一致\n- 满分 {max_score}，小错误适当扣分' }]
                            qs[idx] = { ...q, rubrics }
                            setNewExam({ ...newExam, questions: qs })
                          }}>新增模板</Button>
                        </div>
                      </div>
                    ))}
                    {q.rubrics.length === 0 && (
                      <Button variant="outlined" onClick={() => {
                        const qs = [...newExam.questions]
                        const rubrics = [{ rubric_title: '默认模板', rubric_template: '评分说明：\n- 对比 {solution} 与 {correct_answer}\n- 最终答案 {final_answer} 是否一致\n- 满分 {max_score}，小错误适当扣分' }]
                        qs[idx] = { ...q, rubrics }
                        setNewExam({ ...newExam, questions: qs })
                      }}>添加模板</Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
      <Dialog open={deleteOpen} onClose={() => setDeleteOpen(false)}>
        <DialogTitle>删除考试</DialogTitle>
        <DialogContent>
          <Typography variant="body2">此操作不可撤销，请输入 <span className="mono">Confirm</span> 以确认删除当前考试。</Typography>
          <TextField autoFocus fullWidth margin="dense" value={deleteText} onChange={(e) => setDeleteText(e.target.value)} placeholder="Confirm" />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteOpen(false)}>取消</Button>
          <Button color="error" disabled={deleteText !== 'Confirm'} onClick={async () => {
            if (!draft?.exam_id) return
            await deleteExam(draft.exam_id)
            removeExam(draft.exam_id)
            setDeleteOpen(false)
            setMode('view')
            setDraft(exams[0] || null)
          }}>确认删除</Button>
        </DialogActions>
      </Dialog>
    </div>
  )
}
