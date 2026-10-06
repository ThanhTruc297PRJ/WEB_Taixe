import { useEffect, useRef, useState } from 'react'
import { Card, Empty } from 'antd'

import { INK } from '../config/chartPalette'

const GRID = '#e2e8f0'

const fmt = (v) => Number(v).toLocaleString('vi-VN')

/** Chiều rộng thật của khung chứa, để SVG vẽ đúng tỉ lệ (chữ không bị kéo giãn). */
function useWidth() {
  const ref = useRef(null)
  const [width, setWidth] = useState(0)
  useEffect(() => {
    const el = ref.current
    if (!el) return undefined
    const ro = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width))
    ro.observe(el)
    return () => ro.disconnect()
  }, [])
  return [ref, width]
}

/** Tooltip bám con trỏ, dùng chung cho mọi biểu đồ. */
function useHoverTip() {
  const boxRef = useRef(null)
  const [tip, setTip] = useState(null)
  const show = (event, content) => {
    const box = boxRef.current?.getBoundingClientRect()
    if (!box) return
    setTip({ x: event.clientX - box.left, y: event.clientY - box.top, content })
  }
  const hide = () => setTip(null)
  const node = tip && (
    <div
      style={{
        position: 'absolute',
        left: tip.x,
        top: tip.y,
        transform: `translate(${tip.x > 200 ? 'calc(-100% - 12px)' : '12px'}, -50%)`,
        pointerEvents: 'none',
        zIndex: 5,
        background: '#0f172a',
        color: '#fff',
        fontSize: 12,
        lineHeight: 1.5,
        padding: '6px 10px',
        borderRadius: 6,
        whiteSpace: 'nowrap',
        boxShadow: '0 4px 12px rgba(15,23,42,0.18)',
      }}
    >
      {tip.content}
    </div>
  )
  return { boxRef, show, hide, node }
}

function TipLines({ title, rows }) {
  return (
    <>
      <div style={{ fontWeight: 600, marginBottom: 2 }}>{title}</div>
      {rows.map((r) => (
        <div key={r.label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 8, height: 8, borderRadius: 2, background: r.color }} />
          <span style={{ opacity: 0.8 }}>{r.label}</span>
          <span style={{ marginLeft: 'auto', paddingLeft: 12, fontWeight: 600 }}>{r.value}</span>
        </div>
      ))}
    </>
  )
}

export function ChartCard({ title, subtitle, extra, children }) {
  return (
    <Card
      className="h-full"
      styles={{ body: { padding: '12px 20px 20px' } }}
      title={
        <div style={{ padding: '4px 0' }}>
          <div style={{ fontSize: 15, fontWeight: 600, color: INK.primary }}>{title}</div>
          {subtitle && (
            <div style={{ fontSize: 12, fontWeight: 400, color: INK.secondary }}>{subtitle}</div>
          )}
        </div>
      }
      extra={extra}
    >
      {children}
    </Card>
  )
}

function Legend({ items, total }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, minWidth: 0 }}>
      {items.map((it) => (
        <div
          key={it.key}
          style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}
        >
          <span
            style={{ width: 10, height: 10, borderRadius: 3, background: it.color, flexShrink: 0 }}
          />
          <span style={{ color: INK.secondary, flex: 1, minWidth: 0 }}>{it.label}</span>
          <span style={{ color: INK.primary, fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
            {fmt(it.value)}
          </span>
          <span
            style={{
              color: INK.muted,
              width: 38,
              textAlign: 'right',
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            {total ? `${Math.round((it.value / total) * 100)}%` : '—'}
          </span>
        </div>
      ))}
    </div>
  )
}

/** Biểu đồ tròn khuyết + chú thích có số và %. `data`: [{key,label,value,color}]. */
export function DonutChart({ data, centerValue, centerLabel, emptyText, onSliceClick }) {
  const { boxRef, show, hide, node } = useHoverTip()
  const total = data.reduce((s, d) => s + d.value, 0)
  const R = 70
  const STROKE = 22
  const C = 2 * Math.PI * R

  if (!total) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={emptyText} />
  }

  // Vị trí bắt đầu của từng lát tính trước (không cộng dồn trong lúc render).
  const visible = data
    .filter((d) => d.value > 0)
    .reduce((acc, d) => {
      const start = acc.length ? acc[acc.length - 1].start + acc[acc.length - 1].len : 0
      return [...acc, { ...d, start, len: (d.value / total) * C }]
    }, [])
  return (
    <div
      ref={boxRef}
      style={{ position: 'relative', display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 20 }}
    >
      <svg
        viewBox="0 0 180 180"
        width={164}
        height={164}
        role="img"
        aria-label={data.map((d) => `${d.label}: ${d.value}`).join(', ')}
        style={{ flexShrink: 0 }}
      >
        <g transform="rotate(-90 90 90)">
          {visible.map((d) => {
            const { len } = d
            // Khe 2px màu nền giữa các lát (chỉ khi có từ 2 lát trở lên).
            const gap = visible.length > 1 ? 2 : 0
            const seg = (
              <circle
                key={d.key}
                cx="90"
                cy="90"
                r={R}
                fill="none"
                stroke={d.color}
                strokeWidth={STROKE}
                strokeDasharray={`${Math.max(len - gap, 0.01)} ${C}`}
                strokeDashoffset={-d.start}
                style={{ cursor: onSliceClick ? 'pointer' : 'default' }}
                onMouseMove={(e) =>
                  show(
                    e,
                    <TipLines
                      title={d.label}
                      rows={[
                        {
                          label: 'Số lượng',
                          value: `${fmt(d.value)} (${Math.round((d.value / total) * 100)}%)`,
                          color: d.color,
                        },
                      ]}
                    />,
                  )
                }
                onMouseLeave={hide}
                onClick={() => onSliceClick?.(d)}
              />
            )
            return seg
          })}
        </g>
        <text
          x="90"
          y="88"
          textAnchor="middle"
          style={{ fontSize: 26, fontWeight: 700, fill: INK.primary }}
        >
          {centerValue ?? fmt(total)}
        </text>
        <text x="90" y="108" textAnchor="middle" style={{ fontSize: 11, fill: INK.secondary }}>
          {centerLabel}
        </text>
      </svg>
      <div style={{ flex: '1 1 160px', minWidth: 0 }}>
        <Legend items={data} total={total} />
      </div>
      {node}
    </div>
  )
}

/** Cột ngang xếp hạng (1 dãy số). `rows`: [{key,label,value,sub,color}]. */
export function RankBars({ rows, unit, emptyText, onRowClick }) {
  const { boxRef, show, hide, node } = useHoverTip()
  const max = Math.max(1, ...rows.map((r) => r.value))
  if (!rows.length) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={emptyText} />
  }
  return (
    <div ref={boxRef} style={{ position: 'relative', display: 'flex', flexDirection: 'column', gap: 12 }}>
      {rows.map((r) => (
        <div
          key={r.key}
          role={onRowClick ? 'button' : undefined}
          tabIndex={onRowClick ? 0 : undefined}
          onClick={() => onRowClick?.(r)}
          onMouseMove={(e) =>
            show(
              e,
              <TipLines
                title={r.label}
                rows={[{ label: unit, value: fmt(r.value), color: r.color }]}
              />,
            )
          }
          onMouseLeave={hide}
          style={{ cursor: onRowClick ? 'pointer' : 'default' }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              gap: 8,
              fontSize: 13,
              marginBottom: 4,
            }}
          >
            <span
              style={{
                color: INK.primary,
                fontWeight: 500,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {r.label}
              {r.sub && <span style={{ color: INK.muted, fontWeight: 400 }}> · {r.sub}</span>}
            </span>
            <span style={{ color: INK.primary, fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
              {fmt(r.value)}
            </span>
          </div>
          <div style={{ height: 10, borderRadius: 4, background: '#f1f5f9' }}>
            <div
              style={{
                width: `${(r.value / max) * 100}%`,
                minWidth: 4,
                height: '100%',
                borderRadius: 4,
                background: r.color,
              }}
            />
          </div>
        </div>
      ))}
      {node}
    </div>
  )
}

function niceMax(v) {
  if (v <= 4) return 4
  const pow = 10 ** Math.floor(Math.log10(v))
  const n = v / pow
  const step = n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10
  return step * pow
}

function topRoundedRect(x, y, w, h, r) {
  const rr = Math.min(r, w / 2, h)
  return `M${x},${y + h} V${y + rr} Q${x},${y} ${x + rr},${y} H${x + w - rr} Q${x + w},${y} ${x + w},${y + rr} V${y + h} Z`
}

/**
 * Cột đứng xếp chồng. `rows`: [{label, tipTitle, [seriesKey]: number}],
 * `series`: [{key,label,color}]. `tickEvery`: hiện nhãn trục X mỗi n cột.
 * `formatValue`: định dạng số trên trục Y + tooltip.
 */
export function StackedColumns({
  rows,
  series,
  height = 220,
  tickEvery = 1,
  formatValue = fmt,
  emptyText,
}) {
  const [wrapRef, width] = useWidth()
  const { boxRef, show, hide, node } = useHoverTip()
  const totals = rows.map((r) => series.reduce((s, se) => s + (r[se.key] || 0), 0))
  const hasAny = totals.some((t) => t > 0)

  const LEFT = 52
  const BOTTOM = 24
  const TOP = 8
  const plotW = Math.max(0, width - LEFT)
  const plotH = height - BOTTOM - TOP
  let yMax = niceMax(Math.max(...totals, 0))
  // Vạch giữa luôn là số tròn (VD trần 5 -> 6, vạch 0/3/6).
  if (yMax % 2) yMax += 1
  const ticks = [0, yMax / 2, yMax]
  const slot = rows.length ? plotW / rows.length : 0
  const barW = Math.max(2, Math.min(36, slot * 0.62))
  const y = (v) => TOP + plotH - (v / yMax) * plotH

  return (
    <div ref={boxRef} style={{ position: 'relative' }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, marginBottom: 8 }}>
        {series.map((se) => (
          <span
            key={se.key}
            style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: INK.secondary }}
          >
            <span style={{ width: 10, height: 10, borderRadius: 3, background: se.color }} />
            {se.label}
            <strong style={{ color: INK.primary, fontWeight: 600 }}>
              {formatValue(rows.reduce((s, r) => s + (r[se.key] || 0), 0))}
            </strong>
          </span>
        ))}
      </div>
      <div ref={wrapRef} style={{ width: '100%' }}>
        {!hasAny ? (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={emptyText} />
        ) : (
          width > 0 && (
            <svg width={width} height={height} role="img" aria-label={emptyText}>
              {ticks.map((t) => (
                <g key={t}>
                  <line
                    x1={LEFT}
                    x2={width}
                    y1={y(t)}
                    y2={y(t)}
                    stroke={t === 0 ? '#cbd5e1' : GRID}
                    strokeDasharray={t === 0 ? undefined : '3 3'}
                  />
                  <text
                    x={LEFT - 8}
                    y={y(t) + 4}
                    textAnchor="end"
                    style={{ fontSize: 11, fill: INK.muted, fontVariantNumeric: 'tabular-nums' }}
                  >
                    {formatValue(t)}
                  </text>
                </g>
              ))}
              {rows.map((r, i) => {
                const x = LEFT + i * slot + (slot - barW) / 2
                let acc = 0
                const segs = series.filter((se) => (r[se.key] || 0) > 0)
                return (
                  <g
                    key={r.label}
                    onMouseMove={(e) =>
                      show(
                        e,
                        <TipLines
                          title={r.tipTitle ?? r.label}
                          rows={series.map((se) => ({
                            label: se.label,
                            value: formatValue(r[se.key] || 0),
                            color: se.color,
                          }))}
                        />,
                      )
                    }
                    onMouseLeave={hide}
                  >
                    {/* Vùng bắt chuột cao hết cột, rộng hơn cột cho dễ trỏ. */}
                    <rect x={LEFT + i * slot} y={TOP} width={slot} height={plotH} fill="transparent" />
                    {segs.map((se, si) => {
                      const v = r[se.key]
                      const y0 = y(acc)
                      acc += v
                      const y1 = y(acc)
                      const isTop = si === segs.length - 1
                      // Khe 2px màu nền giữa các đoạn chồng.
                      const h = Math.max(1, y0 - y1 - (isTop ? 0 : 2))
                      return isTop ? (
                        <path key={se.key} d={topRoundedRect(x, y1, barW, h, 4)} fill={se.color} />
                      ) : (
                        <rect key={se.key} x={x} y={y1 + 2} width={barW} height={h} fill={se.color} />
                      )
                    })}
                    {i % tickEvery === 0 && (
                      <text
                        x={LEFT + i * slot + slot / 2}
                        y={height - 6}
                        textAnchor="middle"
                        style={{ fontSize: 11, fill: INK.muted }}
                      >
                        {r.label}
                      </text>
                    )}
                  </g>
                )
              })}
            </svg>
          )
        )}
      </div>
      {node}
    </div>
  )
}

