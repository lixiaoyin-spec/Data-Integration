<?xml version="1.0" encoding="UTF-8"?>
<!-- 选课信息格式转换: 学院原生格式 → 标准集成格式 -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/">
    <Choices>
      <xsl:for-each select="Choices/choice">
        <choice>
          <!-- 学号映射 -->
          <sid>
            <xsl:choose>
              <xsl:when test="Sno"><xsl:value-of select="Sno"/></xsl:when>
              <xsl:when test="sno"><xsl:value-of select="sno"/></xsl:when>
              <xsl:otherwise><xsl:value-of select="sid"/></xsl:otherwise>
            </xsl:choose>
          </sid>
          <!-- 课程号映射 -->
          <cid>
            <xsl:choose>
              <xsl:when test="Cno"><xsl:value-of select="Cno"/></xsl:when>
              <xsl:when test="cno"><xsl:value-of select="cno"/></xsl:when>
              <xsl:otherwise><xsl:value-of select="cid"/></xsl:otherwise>
            </xsl:choose>
          </cid>
          <!-- 成绩映射 -->
          <score>
            <xsl:choose>
              <xsl:when test="Grd"><xsl:value-of select="Grd"/></xsl:when>
              <xsl:when test="grade"><xsl:value-of select="grade"/></xsl:when>
              <xsl:otherwise><xsl:value-of select="score"/></xsl:otherwise>
            </xsl:choose>
          </score>
        </choice>
      </xsl:for-each>
    </Choices>
  </xsl:template>

</xsl:stylesheet>
