import { NavLink, Route, Routes } from 'react-router-dom'
import { useEffect } from 'react'
import ExamConfigPage from './pages/ExamConfigPage'
import UploadPage from './pages/UploadPage'
import GradingPage from './pages/GradingPage'
import AnalyticsPage from './pages/AnalyticsPage'
import TAManagePage from './pages/TAManagePage'
import { useAppStore } from './store/app'
import { mockExams, mockPapers, mockTAs } from './mock'
import { fetchExams, fetchTAs } from './api'

export default function App() {
  const initialized = useAppStore((s) => s.initialized)
  const init = useAppStore((s) => s.init)
  useEffect(() => {
    if (initialized) return
    ;(async () => {
      try {
        const exams = await fetchExams()
        const tas = await fetchTAs().catch(() => mockTAs)
        if (exams.length) init({ exams, papers: mockPapers, tas })
        else init({ exams: mockExams, papers: mockPapers, tas })
      } catch {
        init({ exams: mockExams, papers: mockPapers, tas: mockTAs })
      }
    })()
  }, [initialized, init])
  return (
    <div className="app">
      <header className="header">
        <div className="brand">Smart Rating AI</div>
        <nav className="nav">
          <NavLink to="/config">考试配置/查看</NavLink>
          <NavLink to="/upload">上传试卷</NavLink>
          <NavLink to="/grading">批阅</NavLink>
          <NavLink to="/analytics">成绩分析</NavLink>
          <NavLink to="/ta">助教管理</NavLink>
        </nav>
      </header>
      <main className="main">
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/config" element={<ExamConfigPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/grading" element={<GradingPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/ta" element={<TAManagePage />} />
        </Routes>
      </main>
    </div>
  )
}
