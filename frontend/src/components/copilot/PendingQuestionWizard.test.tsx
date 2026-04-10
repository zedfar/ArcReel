import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { PendingQuestion } from "@/types";
import { PendingQuestionWizard } from "./PendingQuestionWizard";

function makePendingQuestion(overrides: Partial<PendingQuestion> = {}): PendingQuestion {
  return {
    question_id: "q-1",
    questions: [
      {
        header: "Output",
        question: "OutputFormat是什么？",
        multiSelect: false,
        options: [
          { label: "Ringkasan", description: "Output ringkas" },
          { label: "Detail", description: "Penjelasan lengkap" },
        ],
      },
      {
        header: "章节",
        question: "包含哪些部分？",
        multiSelect: true,
        options: [
          { label: "引言", description: "开场上下文" },
          { label: "结论", description: "总结收束" },
        ],
      },
    ],
    ...overrides,
  };
}

describe("PendingQuestionWizard", () => {
  it("renders only the current question and blocks next until answered", () => {
    render(
      <PendingQuestionWizard
        pendingQuestion={makePendingQuestion()}
        answeringQuestion={false}
        error={null}
        onSubmitAnswers={vi.fn()}
      />,
    );

    expect(screen.getByText("Pertanyaan 1/2")).toBeInTheDocument();
    expect(screen.getByText("OutputFormat是什么？")).toBeInTheDocument();
    expect(screen.queryByText("包含哪些部分？")).not.toBeInTheDocument();

    const nextButton = screen.getByRole("button", { name: "下一题" });
    expect(nextButton).toBeDisabled();

    fireEvent.click(screen.getByLabelText("Ringkasan"));
    expect(nextButton).toBeEnabled();

    fireEvent.click(nextButton);
    expect(screen.getByText("Pertanyaan 2/2")).toBeInTheDocument();
    expect(screen.getByText("包含哪些部分？")).toBeInTheDocument();
    expect(screen.queryByText("OutputFormat是什么？")).not.toBeInTheDocument();
  });

  it("keeps answers when navigating backward", () => {
    render(
      <PendingQuestionWizard
        pendingQuestion={makePendingQuestion()}
        answeringQuestion={false}
        error={null}
        onSubmitAnswers={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByLabelText("Detail"));
    fireEvent.click(screen.getByRole("button", { name: "下一题" }));
    fireEvent.click(screen.getByRole("button", { name: "上一步" }));

    expect(screen.getByText("OutputFormat是什么？")).toBeInTheDocument();
    expect(screen.getByLabelText("Detail")).toBeChecked();
  });

  it("validates custom other answers and joins multi-select payloads", () => {
    const onSubmitAnswers = vi.fn();

    render(
      <PendingQuestionWizard
        pendingQuestion={makePendingQuestion({
          questions: [
            {
              header: "章节",
              question: "包含哪些部分？",
              multiSelect: true,
              options: [
                { label: "引言", description: "开场上下文" },
                { label: "结论", description: "总结收束" },
              ],
            },
          ],
        })}
        answeringQuestion={false}
        error={null}
        onSubmitAnswers={onSubmitAnswers}
      />,
    );

    fireEvent.click(screen.getByLabelText("引言"));
    fireEvent.click(screen.getByLabelText("其他"));

    const submitButton = screen.getByRole("button", { name: "Selesai并Submit" });
    expect(submitButton).toBeDisabled();

    fireEvent.change(screen.getByPlaceholderText("Silakan masukkan其他Konten"), {
      target: { value: "附录" },
    });
    expect(submitButton).toBeEnabled();

    fireEvent.click(submitButton);

    expect(onSubmitAnswers).toHaveBeenCalledWith("q-1", {
      "包含哪些部分？": "引言, 附录",
    });
  });

  it("resets local wizard state when question_id changes", () => {
    const { rerender } = render(
      <PendingQuestionWizard
        pendingQuestion={makePendingQuestion()}
        answeringQuestion={false}
        error={null}
        onSubmitAnswers={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByLabelText("Ringkasan"));
    fireEvent.click(screen.getByRole("button", { name: "下一题" }));
    expect(screen.getByText("包含哪些部分？")).toBeInTheDocument();

    rerender(
      <PendingQuestionWizard
        pendingQuestion={makePendingQuestion({ question_id: "q-2" })}
        answeringQuestion={false}
        error={null}
        onSubmitAnswers={vi.fn()}
      />,
    );

    expect(screen.getByText("OutputFormat是什么？")).toBeInTheDocument();
    expect(screen.queryByText("包含哪些部分？")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Ringkasan")).not.toBeChecked();
    expect(screen.getByRole("button", { name: "下一题" })).toBeDisabled();
  });

  it("keeps the action area visible by making question content scrollable", () => {
    render(
      <PendingQuestionWizard
        pendingQuestion={makePendingQuestion({
          questions: [
            {
              header: "超长Pertanyaan",
              question: "这是一个很长的Pertanyaan。".repeat(120),
              multiSelect: false,
              options: [
                { label: "Lanjut", description: "Lanjut处理" },
              ],
            },
          ],
        })}
        answeringQuestion={false}
        error={null}
        onSubmitAnswers={vi.fn()}
      />,
    );

    expect(screen.getByTestId("pending-question-scroll-area")).toHaveClass("overflow-y-auto");
    expect(screen.getByRole("button", { name: "Selesai并Submit" })).toBeInTheDocument();
  });
});
