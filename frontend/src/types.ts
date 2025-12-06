export type Exam = {
  exam_id: string
  title: string
  total_questions: number
  created_at: string
  questions: Array<{
    question_id: number
    max_score: number
    correct_answer: string
    solution_page: number
    final_answer_page: number
    rubrics: Array<{
      rubric_title: string
      rubric_template: string
    }>
  }>
  total_images?: number
}

export type Paper = {
  paper_id: string
  exam_id: string
  test_code: string
  ta_id: number
  file_name: string
  file_url: string
  submitted_at: string
  questions: Array<{
    question_id: number
    solution_image_url: string
    final_answer_image_url: string
    ai_grading: {
      score: number
      explanation: string
      graded_at: string
    }
    manual_score?: number
  }>
}

export type TA = {
  ta_id: number
  ta_name: string
  email: string
}
