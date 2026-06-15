/** Interactive causal graph visualization */

import { useEffect, useRef } from "react"
import { Network } from "vis-network/standalone"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { CausalGraph, CausalNode } from "./types"

interface GraphViewerProps {
  graph: CausalGraph
}

function getNodeColor(nodeType: CausalNode["node_type"]): string {
  const colors = {
    treatment: "#3b82f6", // blue
    outcome: "#22c55e", // green
    confounder: "#eab308", // yellow
    mediator: "#a855f7", // purple
  }
  return colors[nodeType]
}

export function GraphViewer({ graph }: GraphViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const networkRef = useRef<Network | null>(null)

  useEffect(() => {
    if (!containerRef.current || !graph) return

    // Transform causal graph to vis.js format
    const nodes = graph.nodes.map((node) => ({
      id: node.name,
      label: node.label,
      size: 20 + node.strength * 30,
      color: getNodeColor(node.node_type),
      font: { size: 16 },
      title: `${node.label}\nStrength: ${node.strength.toFixed(2)}`,
    }))

    const edges = graph.edges.map((edge) => ({
      from: edge.cause,
      to: edge.effect,
      label: `β=${edge.effect_size.toFixed(2)}`,
      title: `Effect: ${edge.effect_size.toFixed(3)}\nConfidence: ${edge.confidence.toFixed(3)}`,
      arrows: "to",
      width: Math.abs(edge.effect_size) * 8,
      color: {
        color: edge.effect_size > 0 ? "#4ade80" : "#f87171",
        highlight: "#22c55e",
      },
    }))

    const options = {
      nodes: {
        shape: "box",
        margin: 10,
        widthConstraint: { maximum: 200 },
      },
      edges: {
        smooth: { type: "cubicBezier" },
        font: { align: "middle", size: 12 },
      },
      physics: {
        enabled: true,
        barnesHut: {
          gravitationalConstant: -3000,
          centralGravity: 0.3,
        },
      },
      interaction: {
        hover: true,
        tooltipDelay: 200,
        zoomView: true,
      },
    }

    networkRef.current = new Network(
      containerRef.current,
      { nodes, edges },
      options,
    )

    return () => {
      if (networkRef.current) {
        networkRef.current.destroy()
        networkRef.current = null
      }
    }
  }, [graph])

  if (!graph || graph.nodes.length === 0) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-96">
          <p className="text-gray-500">No causal graph available</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="w-full h-full">
      <CardHeader>
        <CardTitle>Causal Relationship Graph</CardTitle>
      </CardHeader>
      <CardContent>
        <div
          ref={containerRef}
          className="causal-graph-container"
          style={{ height: "600px" }}
        />
        <div className="mt-4 flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-500 rounded" />
            <span>Treatment</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-500 rounded" />
            <span>Outcome</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-yellow-500 rounded" />
            <span>Confounder</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-purple-500 rounded" />
            <span>Mediator</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
