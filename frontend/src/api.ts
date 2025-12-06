import { Exam, TA, Paper } from './types'

const BASE = 'http://localhost:8000'

export async function fetchExams(): Promise<Exam[]> {
  const r = await fetch(`${BASE}/exams/`)
  if (!r.ok) throw new Error('failed')
  return r.json()
}

export async function saveExam(exam: Exam): Promise<Exam> {
  const exists = exam.exam_id && exam.exam_id.length > 0
  if (exists) {
    const r = await fetch(`${BASE}/exams/${exam.exam_id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: exam.title,
        total_questions: exam.total_questions,
        total_images: exam.total_images,
        created_at: exam.created_at,
        questions: exam.questions
      })
    })
    if (!r.ok) throw new Error('failed')
    return r.json()
  } else {
    const r = await fetch(`${BASE}/exams/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: exam.title,
        total_questions: exam.total_questions,
        total_images: exam.total_images,
        created_at: exam.created_at,
        questions: exam.questions
      })
    })
    if (!r.ok) throw new Error('failed')
    return r.json()
  }
}

export async function presignUpload(file: File, exam_id?: string, test_code?: string): Promise<{ url: string; key: string; bucket: string }> {
  const r = await fetch(`${BASE}/files/presign`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_name: file.name, content_type: file.type || 'application/octet-stream', exam_id, test_code })
  })
  if (!r.ok) throw new Error('presign failed')
  return r.json()
}

export async function createPaper(paper: Omit<Paper, 'paper_id' | 'submitted_at'>): Promise<Paper> {
  const r = await fetch(`${BASE}/papers/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(paper)
  })
  if (!r.ok) throw new Error('create paper failed')
  return r.json()
}

export async function fetchPapers(exam_id?: string): Promise<Paper[]> {
  const u = new URL(`${BASE}/papers/`)
  if (exam_id) u.searchParams.set('exam_id', exam_id)
  const r = await fetch(u)
  if (!r.ok) throw new Error('failed')
  return r.json()
}

export async function fetchTAs(): Promise<TA[]> {
  const r = await fetch(`${BASE}/tas/`)
  if (!r.ok) throw new Error('failed')
  return r.json()
}

export async function createTA(ta: { ta_name: string; email: string }): Promise<TA> {
  const r = await fetch(`${BASE}/tas/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(ta)
  })
  if (!r.ok) throw new Error('failed')
  return r.json()
}

export async function deleteExam(exam_id: string): Promise<{ deleted: boolean }> {
  const r = await fetch(`${BASE}/exams/${exam_id}`, { method: 'DELETE' })
  if (!r.ok) throw new Error('delete failed')
  return r.json()
}

export async function uploadPaper(file: File, exam_id: string, ta_id: number): Promise<Paper> {
  const fd = new FormData()
  fd.append('exam_id', exam_id)
  fd.append('ta_id', String(ta_id))
  fd.append('file', file)
  const r = await fetch(`${BASE}/upload/paper`, { method: 'POST', body: fd })
  if (!r.ok) throw new Error('upload failed')
  return r.json()
}

export async function getViewUrl(file_url: string): Promise<string> {
  const r = await fetch(`${BASE}/files/view`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_url })
  })
  if (!r.ok) throw new Error('view presign failed')
  const data = await r.json()
  return data.url as string
}

export async function startPipeline(file: File, exam_id: string, ta_id: number): Promise<{ job_id: string; paper_id: string }> {
  const fd = new FormData()
  fd.append('exam_id', exam_id)
  fd.append('ta_id', String(ta_id))
  fd.append('file', file)
  const r = await fetch(`${BASE}/pipeline/run`, { method: 'POST', body: fd })
  if (!r.ok) throw new Error('start pipeline failed')
  return r.json()
}

export async function getPipelineStatus(job_id: string): Promise<{ status: string; paper_id?: string; error?: string }> {
  const u = new URL(`${BASE}/pipeline/status`)
  u.searchParams.set('job_id', job_id)
  const r = await fetch(u)
  if (!r.ok) throw new Error('status failed')
  return r.json()
}

export async function executePipeline(file: File, exam_id: string, ta_id: number): Promise<{ status: string; paper: Paper }> {
  const fd = new FormData()
  fd.append('exam_id', exam_id)
  fd.append('ta_id', String(ta_id))
  fd.append('file', file)
  const r = await fetch(`${BASE}/pipeline/execute`, { method: 'POST', body: fd })
  if (!r.ok) throw new Error('execute pipeline failed')
  return r.json()
}

type AiGrading = { score: number; explanation: string; graded_at: string | null }
type SegImage = { question_id: number; solution_image_url: string; final_answer_image_url: string; ai_grading: AiGrading }
type SegmentResult = { ok?: boolean; images?: SegImage[]; error_code?: string }
export async function processSegment(paper_id: string): Promise<SegmentResult> {
  const r = await fetch(`${BASE}/process/segment`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ paper_id }) })
  if (!r.ok) throw new Error('segment failed')
  return r.json()
}

type SimpleOk = { ok: boolean }
export async function processOCR(paper_id: string): Promise<SimpleOk> {
  const r = await fetch(`${BASE}/process/ocr`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ paper_id }) })
  if (!r.ok) throw new Error('ocr failed')
  return r.json()
}

export async function processGrade(paper_id: string): Promise<SimpleOk & { paper_id: string }> {
  const r = await fetch(`${BASE}/process/grade`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ paper_id }) })
  if (!r.ok) throw new Error('grade failed')
  return r.json()
}
