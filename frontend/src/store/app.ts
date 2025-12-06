import { create } from 'zustand'
import { Exam, Paper, TA } from '../types'

type InitPayload = { exams: Exam[]; papers: Paper[]; tas: TA[] }

type State = {
  initialized: boolean
  exams: Exam[]
  papers: Paper[]
  tas: TA[]
  selectedExamId: string | null
  selectedPaperId: string | null
  selectedTaId: number | null
  init: (p: InitPayload) => void
  selectExam: (id: string | null) => void
  selectTa: (id: number | null) => void
  addPaper: (paper: Paper) => void
  setPapers: (papers: Paper[]) => void
  selectPaper: (id: string | null) => void
  setManualScore: (paperId: string, questionId: number, score: number) => void
  updateExam: (exam: Exam) => void
  addExam: (exam: Exam) => void
  removeExam: (exam_id: string) => void
  updatePaperTestCode: (paperId: string, testCode: string) => void
}

export const useAppStore = create<State>((set) => ({
  initialized: false,
  exams: [],
  papers: [],
  tas: [],
  selectedExamId: null,
  selectedPaperId: null,
  selectedTaId: null,
  init: (p) =>
    set({
      initialized: true,
      exams: p.exams,
      papers: p.papers,
      tas: p.tas,
      selectedExamId: p.exams[0]?.exam_id || null,
      selectedPaperId: p.papers[0]?.paper_id || null,
      selectedTaId: p.tas[0]?.ta_id || null
    }),
  selectExam: (id) => set({ selectedExamId: id }),
  selectTa: (id) => set({ selectedTaId: id }),
  addPaper: (paper) => set((s) => ({ papers: [paper, ...s.papers], selectedPaperId: paper.paper_id })),
  setPapers: (papers) => set({ papers }),
  selectPaper: (id) => set({ selectedPaperId: id }),
  setManualScore: (paperId, questionId, score) =>
    set((s) => ({
      papers: s.papers.map((p) =>
        p.paper_id === paperId
          ? {
              ...p,
              questions: p.questions.map((q) =>
                q.question_id === questionId ? { ...q, manual_score: score } : q
              )
            }
          : p
      )
    })),
  updateExam: (exam) =>
    set((s) => ({ exams: s.exams.map((e) => (e.exam_id === exam.exam_id ? exam : e)) })),
  addExam: (exam) =>
    set((s) => ({ exams: [...s.exams, exam], selectedExamId: exam.exam_id })),
  removeExam: (exam_id) =>
    set((s) => {
      const exams = s.exams.filter((e) => e.exam_id !== exam_id)
      const selectedExamId = exams[0]?.exam_id || null
      return { exams, selectedExamId }
    }),
  updatePaperTestCode: (paperId, testCode) =>
    set((s) => ({
      papers: s.papers.map((p) => (p.paper_id === paperId ? { ...p, test_code: testCode } : p))
    }))
}))
