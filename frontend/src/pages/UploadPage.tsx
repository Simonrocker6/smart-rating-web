import { useEffect, useMemo, useRef, useState } from 'react'
import { useAppStore } from '../store/app'
import { Paper } from '../types'
import { fetchPapers, executePipeline, getViewUrl } from '../api'

function parseTestCode(fileName: string) {
  const base = fileName.replace(/\.pdf$/i, '')
  const parts = base.split('_')
  return parts.slice(1).join('_') || base
}

export default function UploadPage() {
  const exams = useAppStore((s) => s.exams)
  const selectedExamId = useAppStore((s) => s.selectedExamId)
  const selectExam = useAppStore((s) => s.selectExam)
  const tas = useAppStore((s) => s.tas)
  const selectedTaId = useAppStore((s) => s.selectedTaId)
  const selectTa = useAppStore((s) => s.selectTa)
  const papers = useAppStore((s) => s.papers)
  const setPapers = useAppStore((s) => s.setPapers)
  const updatePaperTestCode = useAppStore((s) => s.updatePaperTestCode)
  const addPaper = useAppStore((s) => s.addPaper)
  const selectPaper = useAppStore((s) => s.selectPaper)
  const exam = useMemo(() => exams.find((e) => e.exam_id === selectedExamId) || exams[0], [exams, selectedExamId])
  const [drag, setDrag] = useState(false)
  const [progress, setProgress] = useState<Record<string, string>>({})
  const [results, setResults] = useState<Record<string, { status: string; url?: string }>>({})
  const dirInputRef = useRef<HTMLInputElement | null>(null)
  useEffect(() => {
    if (dirInputRef.current) dirInputRef.current.setAttribute('webkitdirectory', '')
  }, [])
  useEffect(() => {
    if (!exam) return
    (async () => {
      try {
        const list = await fetchPapers(exam.exam_id)
        setPapers(list)
      } catch {
        /* ignore */
      }
    })()
  }, [exam, setPapers])
  const onFiles = (files: FileList) => {
    if (!exam || !selectedTaId) return
    Array.from(files).forEach(async (f) => {
      try {
        setProgress((p0) => ({ ...p0, [f.name]: 'Processing' }))
        const { status, paper } = await executePipeline(f, exam.exam_id, selectedTaId)
        addPaper(paper as Paper)
        selectPaper(paper.paper_id)
        setProgress((p0) => ({ ...p0, [f.name]: status === 'ok' ? 'Success' : 'Segment Error' }))
        setResults((r0) => ({ ...r0, [f.name]: { status, url: paper.file_url } }))
      } catch {
        setProgress((p0) => ({ ...p0, [f.name]: 'Error' }))
      }
    })
  }
  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDrag(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length) onFiles(e.dataTransfer.files)
  }
  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) onFiles(e.target.files)
  }
  return (
    <div className="row">
      <div className="card">
        <div className="grid-3">
          <div className="field">
            <label>选择考试</label>
            <select value={exam?.exam_id} onChange={(e) => selectExam(e.target.value)}>
              {exams.map((e) => (
                <option key={e.exam_id} value={e.exam_id}>{e.title}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>选择 TA</label>
            <select value={selectedTaId ?? ''} onChange={(e) => selectTa(Number(e.target.value))}>
              {tas.map((t) => (
                <option key={t.ta_id} value={t.ta_id}>{t.ta_name}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="title">试卷上传</div>
        <div className={`dropzone ${drag ? 'dragover' : ''}`} onDragOver={(e) => { e.preventDefault(); setDrag(true) }} onDragLeave={() => setDrag(false)} onDrop={onDrop}>
          <div>拖拽 PDF 到此或选择文件</div>
          <input type="file" accept="application/pdf" multiple onChange={onChange} style={{ marginTop: 12 }} />
          <input type="file" multiple onChange={onChange} style={{ marginTop: 12 }} ref={dirInputRef} />
        </div>
      </div>
      <div className="card">
        <div className="title">已上传文件（当前考试）</div>
        <div className="list" style={{ marginTop: 8 }}>
          {papers.filter((p) => p.exam_id === exam?.exam_id).map((p) => (
            <div key={p.paper_id} className="card" style={{ padding: 12 }}>
              <div className="badge">{p.file_name}</div>
              <div className="muted" style={{ marginTop: 6 }}>学生：{p.test_code}</div>
              <div className="muted">提交时间：{new Date(p.submitted_at).toLocaleString()}</div>
              <div className="muted">状态：{progress[p.file_name] || '待处理'}</div>
              {p.file_url && (
                <div className="btnbar" style={{ marginTop: 8 }}>
                  <button
                    className="btn"
                    onClick={async () => {
                      try {
                        const view = await getViewUrl(p.file_url)
                        window.open(view, '_blank', 'noopener,noreferrer')
                      } catch {
                        /* ignore */
                      }
                    }}
                  >查看文件</button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
  // no polling; results are handled per request
