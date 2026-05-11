.class public Lcom/example/MainActivity;
.super Lcom/example/BaseActivity;
.implements Lcom/example/Clickable;
.implements Landroid/view/View$OnClickListener;

.field private count:I
.field private static final TAG:Ljava/lang/String;

# This comment must not be parsed as a directive

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Lcom/example/BaseActivity;-><init>()V
    return-void
.end method

.method public onClick(Landroid/view/View;)V
    .registers 2
    invoke-virtual {p0}, Lcom/example/MainActivity;->getCount()I
    return-void
.end method

.method public getCount()I
    .registers 2
    iget v0, p0, Lcom/example/MainActivity;->count:I
    iput v0, p0, Lcom/example/MainActivity;->count:I
    return v0
.end method

.method public static logEvent(Ljava/lang/String;)V
    .registers 1
    sget-object v0, Lcom/example/MainActivity;->TAG:Ljava/lang/String;
    sput-object v0, Lcom/example/MainActivity;->TAG:Ljava/lang/String;
    return-void
.end method

.method public static scheduleWork(Ljava/lang/String;)V
    .registers 2
    invoke-static {p0}, Lcom/example/WorkManager;->enqueue(Ljava/lang/String;)V
    return-void
.end method

.method public dispatchClick(Landroid/view/View;)V
    .registers 2
    invoke-interface {p1}, Lcom/example/Clickable;->onClick(Landroid/view/View;)V
    return-void
.end method

.method public initFromSuper()V
    .registers 1
    invoke-super {p0}, Lcom/example/BaseActivity;->onResume()V
    return-void
.end method
