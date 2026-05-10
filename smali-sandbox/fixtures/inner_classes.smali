.class public Lcom/example/Outer;
.super Ljava/lang/Object;

.field private value:I

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method public getValue()I
    .registers 2
    iget v0, p0, Lcom/example/Outer;->value:I
    return v0
.end method


.class public Lcom/example/Outer$Inner;
.super Ljava/lang/Object;

.field private outer:Lcom/example/Outer;

.method public constructor <init>(Lcom/example/Outer;)V
    .registers 2
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/example/Outer$Inner;->outer:Lcom/example/Outer;
    return-void
.end method

.method public callOuter()V
    .registers 2
    invoke-virtual {p0}, Lcom/example/Outer;->getValue()I
    return-void
.end method


.class public Lcom/example/Outer$1;
.super Ljava/lang/Object;
.implements Ljava/lang/Runnable;

.method public run()V
    .registers 1
    return-void
.end method
