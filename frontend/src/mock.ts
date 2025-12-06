import { Exam, Paper, TA } from './types'

export const mockExams: Exam[] = [
  {
  exam_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
  title: '微积分期中测验 2025',
  total_questions: 2,
  created_at: '2025-11-20T10:00:00Z',
  questions: [
    {
      question_id: 1,
      max_score: 5.0,
      correct_answer: '[-3, 5]',
      solution_page: 3,
      final_answer_page: 3,
      rubrics: [
        {
          rubric_title: 'Detailed Step-by-Step',
          rubric_template:
            '1. step by step approach:\n- Step1 (2 points): Condition for \\sqrt{5-x} to be defined is 5-x ≥ 0...\n- Step2 (2 points): ...\n- Step3 (1 point): Final interval written as [-3,5].'
        },
        {
          rubric_title: 'Simple Final-Answer Focused',
          rubric_template:
            'Award full {max_score} points if final answer is [-3,5] and student mentions both x≤5 and x≥-3.'
        }
      ]
    },
    {
      question_id: 2,
      max_score: 4.0,
      correct_answer: "f'(x) = 3x^2 - 6x",
      solution_page: 4,
      final_answer_page: 4,
      rubrics: [
        {
          rubric_title: 'Default Rubric',
          rubric_template:
            'Correct derivative earns full {max_score} points. Minor algebra error: -1. Missing chain rule: -2.'
        }
      ]
    }
  ]
  },
  {
    exam_id: 'b2c3d4e5-f6a7-8901-bcde-f234567890ab',
    title: '线性代数期末 2025',
    total_questions: 2,
    created_at: '2025-11-22T10:00:00Z',
    questions: [
      {
        question_id: 1,
        max_score: 5.0,
        correct_answer: 'x_1 = 2, x_2 = -1',
        solution_page: 2,
        final_answer_page: 2,
        rubrics: [
          { rubric_title: 'Default', rubric_template: '解正确得满分，步骤清晰可加 1 分。' }
        ]
      },
      {
        question_id: 2,
        max_score: 4.0,
        correct_answer: 'det(A) = 3',
        solution_page: 3,
        final_answer_page: 3,
        rubrics: [
          { rubric_title: 'Default', rubric_template: '行列式计算正确得满分，符号错误 -1。' }
        ]
      }
    ]
  }
]

export const mockPapers: Paper[] = [
  {
    paper_id: 'p9876543210',
    exam_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    test_code: 'ALICE_101',
    ta_id: 1,
    file_name: 'MIDTERM_ALICE_101.pdf',
    file_url: 'https://example.com/MIDTERM_ALICE_101.pdf',
    submitted_at: '2025-11-25T14:30:00Z',
    questions: [
      {
        question_id: 1,
        solution_image_url: 'https://picsum.photos/600/800?random=1',
        final_answer_image_url: 'https://picsum.photos/600/200?random=2',
        ai_grading: {
          score: 4.5,
          explanation: 'Correct interval but missed justification for x ≥ -3.',
          graded_at: '2025-11-25T15:00:00Z'
        }
      },
      {
        question_id: 2,
        solution_image_url: 'https://picsum.photos/600/800?random=3',
        final_answer_image_url: 'https://picsum.photos/600/200?random=4',
        ai_grading: {
          score: 3.0,
          explanation: 'Derivative correct except sign error in second term.',
          graded_at: '2025-11-25T15:02:00Z'
        }
      }
    ]
  },
  {
    paper_id: 'p1234567890',
    exam_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    test_code: 'BOB_205',
    ta_id: 1,
    file_name: 'MIDTERM_BOB_205.pdf',
    file_url: 'https://example.com/MIDTERM_BOB_205.pdf',
    submitted_at: '2025-11-25T14:45:00Z',
    questions: [
      {
        question_id: 1,
        solution_image_url: 'https://picsum.photos/600/800?random=5',
        final_answer_image_url: 'https://picsum.photos/600/200?random=6',
        ai_grading: {
          score: 4.0,
          explanation: 'Interval nearly correct with minor boundary confusion.',
          graded_at: '2025-11-25T15:05:00Z'
        }
      },
      {
        question_id: 2,
        solution_image_url: 'https://picsum.photos/600/800?random=7',
        final_answer_image_url: 'https://picsum.photos/600/200?random=8',
        ai_grading: {
          score: 2.0,
          explanation: '未使用乘积法则',
          graded_at: '2025-11-25T15:07:00Z'
        }
      }
    ]
  }
  ,
  {
    paper_id: 'p4455667788',
    exam_id: 'b2c3d4e5-f6a7-8901-bcde-f234567890ab',
    test_code: 'CAROL_301',
    ta_id: 2,
    file_name: 'FINAL_CAROL_301.pdf',
    file_url: 'https://example.com/FINAL_CAROL_301.pdf',
    submitted_at: '2025-11-25T16:00:00Z',
    questions: [
      {
        question_id: 1,
        solution_image_url: 'https://picsum.photos/600/800?random=9',
        final_answer_image_url: 'https://picsum.photos/600/200?random=10',
        ai_grading: { score: 4.5, explanation: '步骤清晰，答案正确。', graded_at: '2025-11-25T16:05:00Z' }
      },
      {
        question_id: 2,
        solution_image_url: 'https://picsum.photos/600/800?random=11',
        final_answer_image_url: 'https://picsum.photos/600/200?random=12',
        ai_grading: { score: 3.5, explanation: '符号有轻微错误。', graded_at: '2025-11-25T16:07:00Z' }
      }
    ]
  }
]

export const mockTAs: TA[] = [
  { ta_id: 1, ta_name: '张老师', email: 'zhang@univ.edu' },
  { ta_id: 2, ta_name: '李老师', email: 'li@univ.edu' }
]
