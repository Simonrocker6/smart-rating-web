import { useEffect, useState } from 'react'
import { useAppStore } from '../store/app'
import { fetchTAs, createTA } from '../api'

export default function TAManagePage() {
  const tas = useAppStore((s) => s.tas)
  const setInit = useAppStore((s) => s.init)
  const exams = useAppStore((s) => s.exams)
  const papers = useAppStore((s) => s.papers)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  useEffect(() => {
    (async () => {
      try {
        const list = await fetchTAs()
        console.log("Fetched ta list:")
        setInit({ exams, papers, tas: list })
      } catch {
        /* ignore */
      }
    })()
  }, [])
  const onCreate = async () => {
    if (!name || !email) return
    const ta = await createTA({ ta_name: name, email })
    const list = await fetchTAs()
    setInit({ exams, papers, tas: list })
    setName('')
    setEmail('')
  }
  return (
    <div className="row">
      <div className="card">
        <div className="title">新增助教</div>
        <div className="grid-3" style={{ marginTop: 8 }}>
          <div className="field">
            <label>姓名</label>
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="field">
            <label>邮箱</label>
            <input value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
        </div>
        <div className="btnbar" style={{ marginTop: 8 }}>
          <button className="btn primary" onClick={onCreate}>添加</button>
        </div>
      </div>
      <div className="card">
        <div className="title">助教列表</div>
        <table className="table" style={{ marginTop: 8 }}>
          <thead>
            <tr>
              <th>姓名</th>
              <th>邮箱</th>
              <th>ID</th>
            </tr>
          </thead>
          <tbody>
            {tas.map((t) => (
              <tr key={t.ta_id}>
                <td>{t.ta_name}</td>
                <td>{t.email}</td>
                <td>{t.ta_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
