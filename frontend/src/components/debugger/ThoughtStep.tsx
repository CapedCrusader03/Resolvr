import React from 'react';
import { Thought } from '../../types';
import { BrainCircuit, Search, Calculator, AlertTriangle, RefreshCcw, ClipboardCheck } from 'lucide-react';

interface ThoughtStepProps {
  thought: Thought;
}

const ThoughtStep: React.FC<ThoughtStepProps> = ({ thought }) => {
  const getNodeIcon = (nodeName: string) => {
    switch (nodeName.toLowerCase()) {
      case 'classifier':
        return BrainCircuit;
      case 'retriever':
        return Search;
      case 'calculator':
        return Calculator;
      case 'anomaly_detector':
        return AlertTriangle;
      case 'solver':
        return RefreshCcw;
      case 'reporter':
        return ClipboardCheck;
      default:
        return BrainCircuit;
    }
  };

  const NodeIcon = getNodeIcon(thought.node);

  return (
    <div className={`thought-step step-${thought.node.toLowerCase()}`}>
      <div className="step-header">
        <div className="step-node-badge flex-center">
          <NodeIcon size={12} className="step-badge-icon" />
          <span>{thought.node.toUpperCase()}</span>
        </div>
        <span className="step-type-badge">{thought.type.toUpperCase()}</span>
      </div>
      
      <div className="step-body">
        <pre className="step-content-code">{thought.content}</pre>
      </div>
    </div>
  );
};

export default ThoughtStep;
